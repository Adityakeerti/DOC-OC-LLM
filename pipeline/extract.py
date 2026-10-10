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

SYSTEM_PROMPT = """You are a high-precision Indian academic marksheet extractor. Return ONLY valid JSON matching the schema.

CRITICAL EXTRACTION RULES:

1. CANDIDATE & PARENT DETAILS:
   - Top section reading order:
     * Line 1: 'This is to certify that' or 'according to the Board's record' / 'परिषद् के अभिलेखानुसार' / "Candidate Name" / "Name" followed by CANDIDATE NAME. Extract the complete student name printed on this line (e.g. KUNWAR KAPIL SINGH KARKI, AMAN GULERIYA, BHUMI, ROHIT PATHAK, SAGAR SANGAMESH TANDUR, VANSH JAISWAL).
     * Line 2: 'Son/Daughter of Mrs.' / 'आत्मज/आत्मजा श्रीमती' or 'Mother's Name' / 'माता का नाम' followed by MOTHER'S NAME (e.g. GEETA PATHAK, SMT MAMTA RANI, KARABI RANA, SUMITRA).
     * Line 3: 'and Mr.' / 'एवं श्री' or 'Father's Name' / 'Father's / Guardian's Name' / 'पिता का नाम' followed by FATHER'S NAME (e.g. NAVEEN CHANDRA PATHAK, BALWANT SINGH RANA, RAJENDRA SINGH, SANGAMESH).
   - WARNING: Mother's Name and Father's Name are TWO DIFFERENT PEOPLE. Mother is Mrs./श्रीमती and Father is Mr./श्री. NEVER set Mother's name equal to Father's name!
   - WARNING: NEVER confuse Candidate Name with Father's Name! A candidate cannot have the identical name as their father.
   - Roll Number / Candidate ID:
     * ICSE & ISC (CISCE Class 10 & 12): The candidate's Roll Number is EXCLUSIVELY the 7-digit numeric "Unique ID" (e.g. "7721300", "7396962", "7224142") or Index No. (e.g. "2241966/014", "2238170/061") printed in the candidate information section. Read all 7 digits of "Unique ID" carefully into "roll_no". NEVER extract the document/certificate serial number at the top left/right (e.g. "No. BH 10075963", "BH 10075963", "No. BG 90094366", "BG 90094366", "No. TT 40195250") as roll_no!
     * CBSE: CBSE Roll Numbers are ALWAYS exactly 8 digits under "Roll No." (e.g. 25109039, 25114139, 25115560, 25107204, 25130945). Count all 8 digits carefully; NEVER drop interior zeros (e.g. extract 25109039, NOT 2510939).
     * Karnataka SSLC: Extract the number under "Register No." (e.g. 20140295230), NOT the barcode serial number.
     * State Boards (UBSE, UPMSP, BSEH): Exact full digits under "Roll No." / "Register No." / "Reg. No." / "अनुक्रमांक".
   - Date of Birth (DOB): Format DD-MM-YYYY if present, or null. Cross-check numeric digits with the date in words printed immediately beside it (e.g. "21ST MAY TWO THOUSAND FOUR" -> "21-05-2004", not 25; "06TH OCTOBER" -> "06-10-2004", "31-10-1998").
   - School / Institution: Full school name and code if visible.

2. BOARD AND EXAMINATION IDENTIFICATION:
   - Look carefully at the header crest, title, and state name:
     * If "उत्तर प्रदेश" or "UTTAR PRADESH" or "UP BOARD" or "ALLAHABAD" or "PRAYAGRAJ" or "माध्यमिक शिक्षा परिषद्, उत्तर प्रदेश", board is ALWAYS "Board of High School and Intermediate Education Uttar Pradesh".
     * If "उत्तराखण्ड" or "UTTARAKHAND" or "RAMNAGAR" or "NAINITAL" or "UBSE" or "उत्तराखण्ड विद्यालयी शिक्षा", board is ALWAYS "Board of School Education Uttarakhand".
     * If "हरियाणा" or "HARYANA" or "BSEH" or "BHIWANI", board is ALWAYS "Board of School Education Haryana".
     * If "CENTRAL BOARD OF SECONDARY EDUCATION" or "CBSE" or "केन्द्रीय माध्यमिक शिक्षा बोर्ड", board is ALWAYS "Central Board of Secondary Education".
     * If "COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS" or "CISCE" or "ICSE" or "ISC", board is ALWAYS "Council for the Indian School Certificate Examinations, New Delhi".
     * If "KARNATAKA" or "KSEEB" or "KARNATAKA SECONDARY EDUCATION EXAMINATION BOARD", board is ALWAYS "Karnataka Secondary Education Examination Board".

3. SUBJECTS TABLE & MARKS:
   - CBSE BOARDS (CLASS 10 & 12):
     * Table columns from left to right: [SUB CODE] [SUBJECT NAME] [THEORY] [IA/PR] [TOTAL] [TOTAL IN WORDS] [GRADE].
     * DO NOT skip the 2nd marks column (IA/PR)! Every CBSE subject has both Theory (e.g. 80, 70, 77, 62, 53) and IA/PR (e.g. 20, 20, 20, 20, 17, 30).
     * 1st marks column: THEORY marks (सैद्धान्तिक).
     * 2nd marks column: IA/PR marks (Internal Assessment / Practical). For Computer Applications, IT, or Painting, IA/PR can be up to 70.
     * 3rd marks column: TOTAL marks for that subject (e.g. 100, 90, 97, 82, 70, 96). Cross-check with 'TOTAL IN WORDS'.
     * Extract "theory": theory_str, "practical": practical_str, "total": total_str, "max_marks": "100", "grade": grade_str.

   - STATE BOARDS (Uttarakhand / UP / MP / Intermediate):
     * Table columns from left to right: [SUB CODE] [SUBJECT NAME] [THEORY (सैद्धान्तिक)] [PRACTICAL / IA (प्रायोगिक)] [TOTAL (योग)] [TOTAL IN WORDS] [GRADE / RESULT].
     * 1st marks column = THEORY marks (e.g. "054", "053", "026", "044", "060", "070", "077").
     * 2nd marks column = PRACTICAL marks (e.g. "020", "030", "019"). If blank or dash '-', output "practical": null.
     * 3rd marks column = TOTAL marks for that subject (e.g. "074", "073", "056", "090", "096").
     * "max_marks": "100" for each subject.
     * NEVER put Grand Total (e.g. 419, 356, 425, 450) into individual subject rows!

   - SINGLE-SCORE STATE BOARDS (Haryana BSEH / Karnataka SSLC):
     * Table columns: [SUBJECTS] [MARKS SCORED / OBTAINED / प्राप्तांक] [PASS MARKS 33/35] [MAX MARKS 100/125] [GRADE].
     * The student's scored marks are under the "MARKS SCORED / प्राप्तांक / MARKS OBTAINED" column (e.g. "073", "069", "072", "118", "93", "94").
     * DO NOT confuse Minimum Pass Marks (33, 35) or Maximum Marks (100, 125) with marks scored!
     * "theory": null, "practical": null.
     * "total": the exact student scored marks from the MARKS OBTAINED column.
     * "max_marks": "125" for Karnataka First Language, "100" for all other subjects.
     * "grade": grade or class if present (e.g. "B+", "A+", "DISTINCTION").

   - CISCE BOARDS (ICSE CLASS 10 & ISC CLASS 12):
     * CISCE marksheets have ONLY ONE numeric marks column titled 'Percentage Marks' (e.g. '74 SEVEN FOUR', '50 FIVE ZERO', '47 FOUR SEVEN', '79 SEVEN NINE', '89 EIGHT NINE').
     * The 2-digit number (74, 50, 47, 79, 89) is the subject score. The words beside it ('SEVEN FOUR', 'FIVE ZERO') are just the score written in words.
     * NEVER treat words as practical marks or create fictitious practicals!
     * For every CISCE / ICSE / ISC subject:
       "theory": null, "practical": null, "total": percentage_marks_str, "max_marks": "100", "grade": null (or letter grade).
     * Class 10 ICSE: Extract only the 6 main parent subjects (ENGLISH, HINDI, HISTORY CIVICS & GEOGRAPHY, MATHEMATICS, SCIENCE, and 6th elective). Do not extract component sub-papers.
     * Class 12 ISC: Extract all external examination subjects (ENGLISH, MATHEMATICS, PHYSICS, CHEMISTRY, BIOLOGY, PHYSICAL EDUCATION, etc.) as individual subjects.

   - CBSE CCE / GRADING-ONLY (NO NUMERIC MARKS):
     * If the marksheet displays ONLY letter grades (e.g. "A1", "A2", "B1") and Grade Points (e.g. "10.0", "9.0") with NO numeric marks out of 100:
       Extract: "theory": null, "practical": null, "total": null, "max_marks": null, "grade": grade_str.

   - GENERAL RULES:
     * NEVER extract co-scholastic / grading-only rows with NO numeric marks (such as "WORK EXPERIENCE", "HEALTH & PHYSICAL EDUCATION", "GENERAL STUDIES", "SUPW", "INTERNAL ASSESSMENT").
     * NEVER create subject rows for headers or category labels like "ADDITIONAL SUBJECT", "COMPULSORY", "ELECTIVE", or "RESULT"!
     * "SUB. CODE": 2-3 digit subject code (e.g. 001, 041, 086, 184, 402). Never use code as marks!
     * Output all marks as strings in quotes (e.g. "072", "020", "092", "74", "118").

4. OVERALL RESULT:
   - Status: "PASS", "PASSED", "FAIL", "COMPARTMENT", or "QUALIFIED".
   - Total Obtained: If a numeric grand total is explicitly printed on the document (e.g. in "RESULT: 428/500", "TOTAL: 409", "TOTAL: 568", "TOTAL: 378"), extract that exact number. If NO numeric grand total is printed on the marksheet (e.g. certificates that only state "Result: PASS"), output null! DO NOT invent or guess a grand total.
   - Maximum Marks: If an overall maximum marks is printed (e.g. "500", "600", "625"), extract it; otherwise output null.
   - Percentage: Percentage string if explicitly printed, or null."""

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
