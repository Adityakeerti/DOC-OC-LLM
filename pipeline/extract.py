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
   - Candidate Name: The student's legal name printed directly following "This is to certify that" or "according to the Board's record" / "परिषद् के अभिलेखानुसार" or "Candidate's Name".
     * Example: In "This is to certify that BHUMI", Candidate Name is "BHUMI".
     * Example: In "according to the Board's record ROHIT PATHAK", Candidate Name is "ROHIT PATHAK".
     * WARNING: NEVER confuse Candidate Name with Mother's Name or Father's Name!
   - Mother's Name: Name printed directly following "Mrs." in "Son/Daughter of Mrs. [NAME]" or after "Mother's Name" / "माता का नाम" / "श्रीमती". (e.g. GEETA PATHAK, KARABI RANA, SARIKA RAJPUT).
   - Father's Name: Name printed directly following "Mr." in "and Mr. [NAME]" or after "Father's Name" / "Father's / Guardian's Name" / "पिता/संरक्षक का नाम" / "श्री". (e.g. NAVEEN CHANDRA PATHAK, MAHESH SINGH, BALWANT SINGH RANA).
   - Roll Number: Exact full digits under "Roll No." / "अनुक्रमांक" (preserve all consecutive digits and interior zeros, e.g. "25109039", "21085521", "23405515").
   - Date of Birth (DOB): Format DD-MM-YYYY if present (e.g. "01-11-2005", "19-10-2005", "04-04-2003"), or null.
   - School / Institution: Full school name and code if visible.

2. SUBJECTS TABLE & MARKS (CBSE, ICSE, STATE BOARDS):
   - Only extract real academic subjects (e.g. HINDI, ENGLISH, MATHEMATICS, SCIENCE, SOCIAL SCIENCE, SANSKRIT, INFORMATION TECHNOLOGY).
   - NEVER create subject rows for headers or category labels like "ADDITIONAL SUBJECT", "COMPULSORY", "INTERNAL ASSESSMENT", "SUPW", or "RESULT"!
   - "SUB. CODE": 2-3 digit subject code (e.g. 001, 021, 031, 101, 128, 184). Never use code as marks!
   - Table columns typically appear as:
     [SUB. CODE] | [SUBJECT] | [THEORY] | [PRACTICAL PR.] | [INTERNAL ASSESS. IA] | [TOTAL] | [TOTAL IN WORDS]
   - IN EACH ROW, COUNT HOW MANY NUMBERS ARE PRINTED IN THE MARKS SECTION:
     * If ONLY TWO numbers are printed in that row (e.g. Hindi/English/Sanskrit where practical is blank):
       - First number = THEORY (e.g. "077", "089", "080")
       - PRACTICAL = null (the practical and IA columns are completely blank!)
       - Second number = TOTAL (e.g. "077", "089", "080")
       - DO NOT invent practical marks, DO NOT copy numbers from other rows, and DO NOT add numbers together!
     * If THREE numbers are printed in that row (e.g. Maths, Science, Social Science where practical/IA exists):
       - First number = THEORY (e.g. "077", "072", "075", "058", "74")
       - Second number = PRACTICAL / IA (e.g. "020", "030", "20", "50")
       - Third number = TOTAL (e.g. "097", "092", "095", "078", "94")
     * In ALL cases:
       - The LAST numeric marks column is ALWAYS the Total marks obtained.
       - The Total MUST match the text in the "TOTAL IN WORDS" / "योग (शब्दों में)" column (e.g. "SEVENTY SEVEN" -> "077", "EIGHTY NINE" -> "089", "NINETY SEVEN" -> "097", "NINETY TWO" -> "092", "NINETY FIVE" -> "095", "EIGHTY" -> "080").
       - Total marks for any single subject CAN NEVER exceed 100.
       - Output all marks as strings in quotes to preserve formatting (e.g. "092", "078", "020", "74").
   - "MAX_MARKS": "100" for each subject.

3. OVERALL RESULT:
   - Status: "PASS", "PASSED", "FAIL", or "COMPARTMENT".
   - Total Obtained: Grand total obtained from the overall result section if printed (e.g. "450" if printed "450/500", "409" if "409/500"), or null.
   - Maximum Marks: Total maximum marks across all subjects (e.g. "500", "600"), or null.
   - Percentage: e.g. "90.0%" or null."""

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
