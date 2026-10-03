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
            "required": ["name", "roll_no"]
        },
        "subjects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "theory": {"type": ["number", "null"]},
                    "practical": {"type": ["number", "null"]},
                    "total": {"type": "number"},
                    "max_marks": {"type": ["number", "null"]},
                    "grade": {"type": ["string", "null"]}
                },
                "required": ["name", "total"]
            }
        },
        "result": {
            "type": "object",
            "properties": {
                "total_obtained": {"type": ["number", "null"]},
                "maximum_marks": {"type": ["number", "null"]},
                "percentage": {"type": ["string", "null"]},
                "status": {"type": "string"}
            },
            "required": ["status"]
        }
    },
    "required": ["board", "examination", "student_info", "subjects", "result"]
}


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a high-precision marksheet data extractor. You receive an image of an Indian
education board marksheet and return ONLY valid JSON matching the schema.

CRITICAL RESOLUTION RULES:
1. CANDIDATE NAME RESOLUTION:
   - On CBSE and State Board certificates, the student's name appears directly after "This is to certify that" or "Name of Candidate" or "Candidate's Name".
   - "Mother's Name" and "Father's Name" appear below. NEVER assign the mother's or father's name as the candidate name!
2. MARKS NOTATION:
   - Never output numbers with leading zeros (write 77, NOT 077).
   - If practical / internal assessment is present, separate theory and practical.
3. SUBJECT MARKS ("total" vs "max_marks"):
   - "total" MUST BE MARKS OBTAINED by the candidate (e.g. theory 62 + practical 20 = total 82). NEVER assign maximum marks (like 100) as the total obtained!
   - "max_marks" is the total possible marks (typically 100).
   - Extract every evaluated subject row. Keep subject names in clean English.
4. DO NOT invent data. If a field is not present or unreadable, use null."""

USER_PROMPT = "Extract all data from this marksheet image into strict JSON according to the schema and layout rules."


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
