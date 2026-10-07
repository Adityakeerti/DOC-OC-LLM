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
     * Line 2: 'Son/Daughter of Mrs.' / 'आत्मज/आत्मजा श्रीमती' or 'Mother's Name' / 'माता का नाम' followed by MOTHER'S NAME.
     * Line 3: 'and Mr.' / 'एवं श्री' or 'Father's Name' / 'Father's / Guardian's Name' / 'पिता का नाम' followed by FATHER'S NAME.
   - WARNING: NEVER confuse Candidate Name with Father's Name! A candidate cannot have the identical name as their father.
   - Roll Number: Exact full digits under "Roll No." / "अनुक्रमांक" (preserve all consecutive digits and interior zeros).
   - Date of Birth (DOB): Format DD-MM-YYYY if present, or null.
   - School / Institution: Full school name and code if visible.

2. SUBJECTS TABLE & MARKS (CBSE, ICSE, STATE BOARDS):
   - Extract ALL academic subject rows (e.g. HINDI, ENGLISH, MATHEMATICS, SCIENCE, SOCIAL SCIENCE, SANSKRIT, PHYSICS, CHEMISTRY, PAINTING, PHYSICAL EDUCATION, INFORMATION TECHNOLOGY).
   - NEVER extract co-scholastic / grading-only rows that have NO numeric marks (such as "WORK EXPERIENCE", "HEALTH & PHYSICAL EDUCATION", "GENERAL STUDIES", "SUPW", "INTERNAL ASSESSMENT").
   - NEVER create subject rows for headers or category labels like "ADDITIONAL SUBJECT", "COMPULSORY", "ELECTIVE", or "RESULT"!
   - "SUB. CODE": 2-3 digit subject code (e.g. 001, 021, 031, 101, 128, 184). Never use code as marks!
   - READ EACH SUBJECT ROW FROM LEFT TO RIGHT:
     * 1st marks column: THEORY marks (सैद्धान्तिक / लिखित).
     * 2nd marks column: PRACTICAL or INTERNAL ASSESSMENT (IA/PR) marks. If that cell is blank, empty, or a dash '-', output null.
     * 3rd marks column: TOTAL marks for that subject. Cross-check with 'TOTAL IN WORDS' column in that row to ensure exact match.
   - WARNING: DO NOT put the grand total into individual subject marks! Every single subject has its own marks (<= 100).
   - "MAX_MARKS": "100" for each subject.
   - Output all marks as strings in quotes (e.g. "072", "020", "092", "74").

3. OVERALL RESULT:
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
