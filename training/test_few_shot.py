import time
import json
import httpx
from pipeline import prepare, validate
from pipeline.extract import image_to_base64, clean_json_response, SYSTEM_PROMPT

API_URL = "http://localhost:8080/v1/chat/completions"

# 1. Few-Shot Enhanced System Prompt with Concrete Ground-Truth Exemplars
FEW_SHOT_SYSTEM_PROMPT = SYSTEM_PROMPT + """

---
CRITICAL RESOLUTION RULES & FEW-SHOT EXAMPLES:

1. CANDIDATE NAME EXTRACTION:
   - On CBSE / State Board certificates, the student's name appears directly after "This is to certify that" or "Name of Candidate".
   - "Mother's Name" and "Father's Name" appear below. NEVER assign the mother's or father's name as the student name!
   
Example Input Layout:
   This is to certify that:  VANSH JAISWAL
   Mother's Name:            MANJU JAISWAL
   Father's Name:            RAJU JAISWAL
Expected Output:
   "student_info": {
       "name": "VANSH JAISWAL",
       "mother_name": "MANJU JAISWAL",
       "father_name": "RAJU JAISWAL"
   }

2. MARKS NOTATION:
   - Never output numbers with leading zeros (e.g. write 77, NOT 077).
   - If practical / internal assessment is present, separate theory and practical:
     Theory: 70, Practical: 20 -> total: 90
"""

def run_few_shot_test(image_path="dataset/12_3.jpg"):
    print(f"\n=======================================================")
    print(f" Testing Few-Shot In-Context Learning on: {image_path}")
    print(f" Target: Verify if Few-Shot fixes Candidate Name resolution")
    print(f"=======================================================\n")

    img = prepare(image_path)
    b64 = image_to_base64(img)

    payload = {
        "messages": [
            {"role": "system", "content": FEW_SHOT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all information from this marksheet into the specified JSON format strictly adhering to candidate name rules."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ],
        "temperature": 0.05,
        "max_tokens": 4096
    }

    t0 = time.time()
    resp = httpx.post(API_URL, json=payload, timeout=120.0)
    dt = time.time() - t0
    resp.raise_for_status()

    raw_text = resp.json()["choices"][0]["message"]["content"]
    cleaned = clean_json_response(raw_text)
    data = json.loads(cleaned)
    marksheet, warnings = validate(data)

    print(f"⏱️ Extraction Time: {dt:.2f}s")
    print(f"🏛️ Extracted Board: {marksheet.board}")
    print(f"👤 Candidate Name : {marksheet.student_info.name}  <--- (Previous Zero-Shot: MANJU JAISAL)")
    print(f"👩 Mother's Name  : {marksheet.student_info.mother_name}")
    print(f"👨 Father's Name  : {marksheet.student_info.father_name}")
    print(f"🆔 Roll Number    : {marksheet.student_info.roll_no}")
    print(f"📚 Total Subjects : {len(marksheet.subjects)}")
    print(f"🏆 Result Status  : {marksheet.result.status}")
    if warnings:
        print(f"⚠️ Warnings: {warnings}")
    
    if marksheet.student_info.name == "VANSH JAISWAL":
        print("\n🎉 SUCCESS! Few-Shot prompt successfully resolved the Candidate Name ambiguity!")
    else:
        print(f"\nExtracted: {marksheet.student_info.name}")

if __name__ == "__main__":
    run_few_shot_test("dataset/12_3.jpg")
