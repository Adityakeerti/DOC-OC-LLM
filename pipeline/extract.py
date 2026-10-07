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
     * Line 1: 'This is to certify that' or 'according to the Board's record' / 'परिषद् के अभिलेखानुसार' followed by CANDIDATE NAME. Extract the complete student name printed on this line (e.g. KUNWAR KAPIL SINGH KARKI, AMAN GULERIYA, BHUMI, ROHIT PATHAK).
     * Line 2: 'Son/Daughter of Mrs.' / 'आत्मज/आत्मजा श्रीमती' or 'Mother's Name' / 'माता का नाम' followed by MOTHER'S NAME (e.g. GEETA PATHAK, SMT MAMTA RANI, KARABI RANA).
     * Line 3: 'and Mr.' / 'एवं श्री' or 'Father's Name' / 'Father's / Guardian's Name' / 'पिता का नाम' followed by FATHER'S NAME (e.g. NAVEEN CHANDRA PATHAK, BALWANT SINGH RANA, RAJENDRA SINGH).
   - WARNING: Mother's Name and Father's Name are TWO DIFFERENT PEOPLE. Mother is Mrs./श्रीमती and Father is Mr./श्री. NEVER set Mother's name equal to Father's name!
   - WARNING: NEVER confuse Candidate Name with Father's Name! A candidate cannot have the identical name as their father.
   - Roll Number:
     * Exact full digits under "Roll No." / "अनुक्रमांक".
     * CBSE Roll Numbers are ALWAYS exactly 8 digits (e.g. 25109039, 25114139, 25115560, 25107204, 25130945). Count all 8 digits carefully; NEVER drop interior zeros (e.g. extract 25109039, NOT 2510939).
   - Date of Birth (DOB): Format DD-MM-YYYY if present, or null. Cross-check numeric digits with the date in words printed immediately beside it (e.g. "21ST MAY TWO THOUSAND FOUR" -> "21-05-2004", not 25; "06TH OCTOBER" -> "06-10-2004"). Always verify against the printed words.
   - School / Institution: Full school name and code if visible.

2. BOARD AND EXAMINATION IDENTIFICATION:
   - Look at the crest, watermark, and header:
     * If "HARYANA" or "BSEH" or "हरियाणा", board is "Board of School Education Haryana".
     * If "UBSE" or "UTTARAKHAND" or "उत्तराखण्ड", board is "Uttarakhand Board of School Education" (NOT Uttar Pradesh!).
     * If "UP BOARD" or "UTTAR PRADESH" or "माध्यमिक शिक्षा परिषद्, उत्तर प्रदेश", board is "Board of High School and Intermediate Education Uttar Pradesh".
     * If "CENTRAL BOARD OF SECONDARY EDUCATION", board is "Central Board of Secondary Education".
     * If "COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS", board is "Council for the Indian School Certificate Examinations, New Delhi".

3. SUBJECTS TABLE & MARKS (CBSE, ICSE, STATE BOARDS):
   - ICSE (CLASS 10 CISCE):
     * Extract ONLY the 6 MAIN academic subjects: 'ENGLISH', 'HINDI' (or second language), 'HISTORY, CIVICS & GEOGRAPHY', 'MATHEMATICS', 'SCIENCE', and the elective/6th subject (e.g. 'COMPUTER APPLICATIONS', 'PHYSICAL EDUCATION', 'COMMERCIAL STUDIES').
     * In Class 10 ICSE, DO NOT extract component papers ('ENGLISH LANGUAGE', 'LITERATURE IN ENGLISH', 'HISTORY & CIVICS', 'GEOGRAPHY', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY') as separate rows.
     * For ICSE parent subjects, the total marks and grade are printed under 'PERCENTAGE MARKS' column (e.g. '89 EIGHT NINE' -> 89, '86 EIGHT SIX' -> 86, '80 EIGHT ZERO' -> 80).
   - ISC & SENIOR SECONDARY (CLASS 12 ALL BOARDS):
     * In Class 12, PHYSICS, CHEMISTRY, BIOLOGY, and MATHEMATICS are INDEPENDENT academic subjects (each out of 100 max marks). DO NOT merge them into Science.
   - CBSE BOARDS:
     * Table columns from left to right: [SUB CODE] [SUBJECT NAME] [THEORY] [IA/PR] [TOTAL] [TOTAL IN WORDS] [GRADE].
     * DO NOT skip the 2nd marks column (IA/PR)! Every CBSE subject has both Theory (e.g. 65, 48, 53) and IA/PR (e.g. 17, 18, 20, 64).
     * 1st marks column: THEORY marks (सैद्धान्तिक).
     * 2nd marks column: IA/PR marks (Internal Assessment / Practical). For Computer Applications, IT, or Painting, IA/PR can be up to 70.
     * 3rd marks column: TOTAL marks for that subject. Cross-check with 'TOTAL IN WORDS'.
   - STATE BOARDS (Uttarakhand / UP / Haryana):
     * Follow the 2-column or 3-column layout. If practical/IA is blank or dash '-', output null.
   - GENERAL RULES:
     * NEVER extract co-scholastic / grading-only rows with NO numeric marks (such as "WORK EXPERIENCE", "HEALTH & PHYSICAL EDUCATION", "GENERAL STUDIES", "SUPW", "INTERNAL ASSESSMENT").
     * NEVER create subject rows for headers or category labels like "ADDITIONAL SUBJECT", "COMPULSORY", "ELECTIVE", or "RESULT"!
     * "SUB. CODE": 2-3 digit subject code (e.g. 001, 041, 086, 184). Never use code as marks!
     * "MAX_MARKS": "100" for each subject.
     * Output all marks as strings in quotes (e.g. "072", "020", "092", "74").

4. OVERALL RESULT:
   - Status: "PASS", "PASSED", "FAIL", or "COMPARTMENT".
   - Total Obtained: If a numeric grand total is explicitly printed on the document (e.g. in "RESULT: 428/500" or "TOTAL: 409"), extract that exact number. If NO numeric grand total is printed on the marksheet (e.g. certificates that only state "Result: PASS"), output null! DO NOT invent or guess a grand total.
   - Maximum Marks: If an overall maximum marks is printed (e.g. "500"), extract it; otherwise output null.
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
