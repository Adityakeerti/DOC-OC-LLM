"""
extract.py — Send a marksheet image to a local VLM and get structured JSON.

Connects to llama-server (OpenAI-compatible API) running locally.
The VLM reads the marksheet image directly and returns a JSON object
with student info, subjects, marks, and results.

No OCR, no regex — the model understands the document visually.
"""

import base64
import io
import json
import re

import httpx
from PIL import Image


# ── Config ────────────────────────────────────────────────────────────────────

API_URL = "http://localhost:8080/v1/chat/completions"
TIMEOUT = 120.0  # seconds — VLM can take a while on complex marksheets


# ── Prompt ────────────────────────────────────────────────────────────────────
# This is the core engineering of the project.
# The prompt tells the VLM exactly what JSON structure to produce.

SYSTEM_PROMPT = """You are a marksheet data extractor. You receive an image of an Indian
education board marksheet and must return ONLY valid JSON.

Use this exact structure:
{
  "board": "string",
  "examination": "string",
  "student_info": {
    "name": "string",
    "roll_no": "string",
    "father_name": "string or null",
    "mother_name": "string or null",
    "school_name": "string or null",
    "dob": "string or null"
  },
  "subjects": [
    {
      "name": "string",
      "theory": number or null,
      "practical": number or null,
      "total": number,
      "max_marks": number or null,
      "grade": "string or null"
    }
  ],
  "result": {
    "total_obtained": number or null,
    "maximum_marks": number or null,
    "percentage": "string or null",
    "status": "PASS or FAIL or COMPARTMENT"
  }
}

Rules:
- Return ONLY the JSON object, nothing else
- Use null for anything not visible or unreadable
- Subject names must be clean English
- Marks must be numbers, not strings
- Do NOT invent or guess any data"""

USER_PROMPT = "Extract all data from this marksheet image."


# ── Helper ────────────────────────────────────────────────────────────────────

def image_to_base64(image: Image.Image) -> str:
    """Convert a PIL Image to a base64-encoded JPEG string."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def clean_json_response(text: str) -> str:
    """Extract and sanitize JSON object substring from model response."""
    text = text.strip()
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

    # Build OpenAI-compatible chat request with image
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
        "temperature": 0.1,     # Low = consistent, deterministic output
        "max_tokens": 4096,     # Enough for even large marksheets
    }

    # Send to local llama-server
    try:
        response = httpx.post(API_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
    except httpx.ConnectError:
        raise RuntimeError(
            "Cannot connect to VLM server. "
            "Start it first: ./start_server.sh"
        )

    # Parse response
    content = response.json()["choices"][0]["message"]["content"]
    content = clean_json_response(content)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"VLM returned invalid JSON: {e}\nRaw: {content[:500]}")
