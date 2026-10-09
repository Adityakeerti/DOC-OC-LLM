"""
extract.py — Send a marksheet image to a local VLM and get structured JSON.

Connects to llama-server (OpenAI-compatible API) running locally.
The VLM reads the marksheet image directly and returns a JSON object
with student info, subjects, marks, and results.

Engineered with:
  1. C++ GBNF JSON Schema constrained decoding (zero parsing/syntax errors)
  2. In-context layout disambiguation rules (candidate name vs parent name)
  3. Automatic leading-zero and JSON formatting sanitation
"""

import base64
import io
import json
import re

import httpx
from PIL import Image


# ── Config ────────────────────────────────────────────────────────────────────

API_URL = "http://localhost:8080/v1/chat/completions"
TIMEOUT = 120.0  # seconds


# ── JSON Schema Constraint ────────────────────────────────────────────────────

MARKSHEET_SCHEMA = {
    "type": "object",
    "properties": {
        "board": {"type": "string"},
        "examination": {"type": "string"},
        "student_info": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "roll_no": {"type": "string"},
                "father_name": {"type": ["string", "null"]},
                "mother_name": {"type": ["string", "null"]},
                "school_name": {"type": ["string", "null"]},
                "dob": {"type": ["string", "null"]}
            },
            "required": ["name", "roll_no", "father_name", "mother_name", "school_name", "dob"]
        },
        "subjects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "theory": {"type": ["string", "null"]},
                    "practical": {"type": ["string", "null"]},
                    "total": {"type": ["string", "null"]},
                    "max_marks": {"type": ["string", "null"]},
                    "grade": {"type": ["string", "null"]}
                },
                "required": ["name", "theory", "practical", "total", "max_marks", "grade"]
            }
        },
        "result": {
            "type": "object",
            "properties": {
                "total_obtained": {"type": ["string", "null"]},
                "maximum_marks": {"type": ["string", "null"]},
                "percentage": {"type": ["string", "null"]},
                "status": {"type": "string"}
            },
            "required": ["status"]
        }
    },
    "required": ["board", "examination", "student_info", "subjects", "result"]
}


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a high-precision Universal Indian Academic Marksheet & Certificate Extractor. Return ONLY valid JSON matching the schema.

CRITICAL EXTRACTION RULES:

1. CANDIDATE & PARENT DETAILS:
   - Reading order & labels:
     * Candidate Name: Full student name printed under "Candidate Name" / "Name" / "परीक्षार्थी का नाम" / "This is to certify that" / "परिषद् के अभिलेखानुसार" (e.g. SAGAR SANGAMESH TANDUR, KUNWAR KAPIL SINGH KARKI, AMAN GULERIYA, ROHIT PATHAK).
     * Mother's Name: Name under "Mother's Name" / "Son/Daughter of Mrs." / "माता का नाम" (e.g. SUMITRA, GEETA PATHAK, SMT MAMTA RANI).
     * Father's Name: Name under "Father's Name" / "Father's / Guardian's Name" / "and Mr." / "पिता का नाम" (e.g. SANGAMESH, NAVEEN CHANDRA PATHAK, RAJENDRA SINGH).
   - WARNING: Mother and Father are TWO DIFFERENT PEOPLE. Mother is Mrs./श्रीमती and Father is Mr./श्री. NEVER set Mother's name equal to Father's name.
   - WARNING: NEVER confuse Candidate Name with Father's Name!
   - Roll / Register Number:
     * Extract the student's unique academic exam number under "Roll No." / "Register No." / "Reg. No." / "अनुक्रमांक" / "पंजीकरण संख्या" / "Index No." / "Unique ID" (e.g. 20140295230, 25109039, 22164964).
     * NEVER confuse with top-corner barcode numbers or certificate serial print numbers (e.g. 13074996, S.No.)!
     * CBSE Roll Numbers are ALWAYS exactly 8 digits. Count all 8 digits carefully without dropping interior zeros.
   - Date of Birth (DOB): Format DD-MM-YYYY if present, or null. Cross-check numeric digits with the date in words printed beside it (e.g. "31-10-1998", "21-05-2004").
   - School / Institution: Full school name and code if visible.

2. BOARD AND EXAMINATION IDENTIFICATION:
   - Identify the issuing authority accurately from crest, header, and watermark:
     * "Karnataka Secondary Education Examination Board" / "Karnataka School Examination and Assessment Board" (KSEEB / KSEAB / SSLC)
     * "Central Board of Secondary Education" (CBSE)
     * "Council for the Indian School Certificate Examinations, New Delhi" (CISCE / ICSE / ISC)
     * "Board of School Education Haryana" (BSEH)
     * "Uttarakhand Board of School Education" (UBSE)
     * "Board of High School and Intermediate Education Uttar Pradesh" (UPMSP)
     * "Maharashtra State Board of Secondary and Higher Secondary Education" (MSBSHSE)
     * Other respective State Board / Council names.

3. UNIVERSAL SUBJECTS TABLE & COLUMN RECOGNITION:
   - Carefully examine the column headers before extracting marks:
     * "MAX MARKS" / "MAX." / "पूर्णांक" / "MAXIMUM": Extract into "max_marks" (e.g. "100", "125", "50", "75", "200"). NEVER put Maximum Marks into "theory" or "total"!
     * "MIN MARKS" / "MIN." / "PASS MARKS" / "उत्तीर्णांक": Minimum threshold to pass (e.g. "33", "35", "44"). DO NOT extract Minimum Pass Marks as marks obtained; NEVER put them into "practical", "theory", or "total"!
     * "MARKS OBTAINED" / "SECURED" / "प्राप्तांक" / "TOTAL" / "योग": The actual marks scored by the candidate in that subject. Extract into "total".
     * "THEORY" / "WRITTEN" / "EXTERNAL" / "सैद्धान्तिक" / "लिखित": Component written exam marks. Extract into "theory".
     * "PRACTICAL" / "INTERNAL ASSESSMENT" / "IA" / "PR" / "CCE" / "PROJECT" / "प्रायोगिक" / "आन्तरिक": Lab or internal assessment marks. Extract into "practical".
     * "GRADE" / "CLASS": Letter grade (e.g. "A1", "B2", "A+") or division class (e.g. "DISTINCTION", "FIRST CLASS").

   - BOARD-SPECIFIC LAYOUT GUIDELINES:
     * Pattern A: Single-Score / State Boards (e.g. Karnataka SSLC, State Boards):
       Columns: [SUBJECT] [MAX MARKS] [MIN MARKS] [MARKS OBTAINED] [CLASS/GRADE].
       CRITICAL: In this layout, there are NO separate theory or practical exams.
       - "theory": MUST BE null!
       - "practical": MUST BE null!
       - "total": The student's actual scored marks from the MARKS OBTAINED column (e.g. "118", "93", "94", "82", "85", "96").
       - "max_marks": The maximum marks for that subject (e.g. "125" for First Language, "100" for other subjects).
       - "grade": Grade or classification if present (or null).
       - NEVER copy Max Marks into "theory" and NEVER copy Min Marks into "practical"!
     * Pattern B: Split Theory + Practical (CBSE, ISC, UP Board, UBSE, Haryana):
       Extract: "theory" = theory mark, "practical" = practical/IA mark, "total" = total subject mark, "max_marks" = subject max (usually "100").
     * Pattern C: ICSE (Class 10 CISCE):
       Extract ONLY the 6 main parent subjects ('ENGLISH', second language, 'HISTORY, CIVICS & GEOGRAPHY', 'MATHEMATICS', 'SCIENCE', 6th elective). Extract the overall subject marks from the 'PERCENTAGE MARKS' column. Do NOT create separate rows for sub-papers ('PHYSICS', 'CHEMISTRY', 'BIOLOGY', etc.).
     * Pattern D: ISC (Class 12 CISCE):
       PHYSICS, CHEMISTRY, BIOLOGY, and MATHEMATICS are INDEPENDENT 100-mark subjects. DO NOT merge them into Science.

   - GENERAL TABLE CLEANING RULES:
     * NEVER extract co-scholastic / grading-only rows with NO numeric marks (e.g. "WORK EXPERIENCE", "HEALTH & PHYSICAL EDUCATION", "GENERAL STUDIES", "SUPW", "INTERNAL ASSESSMENT").
     * NEVER create subject rows for headers or category labels like "ADDITIONAL SUBJECT", "COMPULSORY", "ELECTIVE", or "RESULT".
     * Output all marks as strings in quotes (e.g. "118", "93", "82", "072", "20").

4. OVERALL RESULT & AGGREGATES:
   - "status": "PASS", "PASSED", "FAIL", "FAILED", "COMPARTMENT", or "DISTINCTION".
   - "total_obtained": Exact numeric grand total if explicitly printed on the certificate (e.g. "568", "432", "409"), else null.
   - "maximum_marks": Exact grand maximum marks if printed (e.g. "625", "500", "600"), else null.
   - "percentage": Percentage string if explicitly printed on the document (e.g. "90.88%", "72.0%"), else null."""

USER_PROMPT = "Extract all marksheet data into strict JSON following the schema and disambiguation rules."


# ── Helpers ───────────────────────────────────────────────────────────────────

def image_to_base64(image: Image.Image) -> str:
    """Convert a PIL Image to a base64-encoded JPEG string."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def clean_json_response(text: str) -> str:
    """Extract and sanitize JSON object substring from model response."""
    text = text.strip()
    # Strip leading zeros from numeric values (e.g. ": 020" -> ": 20")
    text = re.sub(r'([:,\[]\s*)0+([1-9][0-9]*)', r'\1\2', text)
    
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        # Remove trailing commas before } or ]
        candidate = re.sub(r",\s*([\]}])", r"\1", candidate)
        return candidate
    return text


# ── Main Function ─────────────────────────────────────────────────────────────

def extract(image: Image.Image) -> dict:
    """
    Send a marksheet image to the local VLM and get structured data back.

    Args:
        image: Preprocessed PIL Image of the marksheet

    Returns:
        dict with keys: board, student_info, subjects, result

    Raises:
        RuntimeError: If the VLM is unreachable or returns invalid JSON
    """
    b64 = image_to_base64(image)

    payload = {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                        },
                    },
                ],
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "marksheet",
                "strict": True,
                "schema": MARKSHEET_SCHEMA,
            }
        },
        "temperature": 0.05,
        "max_tokens": 4096,
    }

    try:
        response = httpx.post(API_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
    except httpx.ConnectError:
        raise RuntimeError(
            "Cannot connect to VLM server. "
            "Start it first: ./start_server.sh"
        )

    content = response.json()["choices"][0]["message"]["content"]
    content = clean_json_response(content)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"VLM returned invalid JSON: {e}\nRaw: {content[:500]}")
