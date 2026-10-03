import os
import sys
import time
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app import app
from pipeline import prepare, extract, validate

def run_all_tests():
    output_lines = []
    def log(msg=""):
        print(msg)
        output_lines.append(msg)

    log("=" * 80)
    log("               DOC-OC v6 — PIPELINE VERIFICATION & BENCHMARK")
    log("=" * 80)
    log(f"Execution Date : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("Model In Use   : Gemma-4-E2B (Local VLM via llama-server on port 8080)")
    log("Inference Mode : Direct Vision-Language Model Extraction (Zero OCR / Zero Regex)")
    log("=" * 80)
    log()

    # 1. FastAPI Endpoint Test
    log("--------------------------------------------------------------------------------")
    log("TEST 1: FastAPI Endpoint Verification (POST /process)")
    log("--------------------------------------------------------------------------------")
    client = TestClient(app)
    sample_file = Path("dataset/10_1.jpg")
    if sample_file.exists():
        t0 = time.time()
        with open(sample_file, "rb") as f:
            response = client.post("/process", files={"file": ("10_1.jpg", f, "image/jpeg")})
        dt = time.time() - t0
        log(f"HTTP Status Code : {response.status_code}")
        if response.status_code == 200:
            res_json = response.json()
            log(f"Response Status  : SUCCESS in {dt:.2f}s")
            log(f"Timing Breakdown : Preprocess: {res_json['timing']['preprocess']}s | Extract: {res_json['timing']['extract']}s | Validate: {res_json['timing']['validate']}s")
            log(f"Extracted Board  : {res_json['data'].get('board')}")
            log(f"Candidate Name   : {res_json['data']['student_info'].get('name')}")
            log(f"Total Subjects   : {len(res_json['data'].get('subjects', []))}")
            log(f"Overall Result   : {res_json['data']['result'].get('status')}")
            log("API Test Result  : PASSED [OK]")
        else:
            log(f"API Test Result  : FAILED with {response.text}")
    log()

    # 2. Pipeline Test Across Marksheet Dataset
    log("--------------------------------------------------------------------------------")
    log("TEST 2: Diverse Marksheet Extraction Across Dataset")
    log("--------------------------------------------------------------------------------")
    
    # Select a diverse set of 8 marksheets: 4 from Class 10th and 4 from Class 12th
    test_files = [
        "dataset/10_1.jpg",
        "dataset/10_2.jpg",
        "dataset/10_3.jpg",
        "dataset/10_4.jpg",
        "dataset/12_1.jpg",
        "dataset/12_2.jpg",
        "dataset/12_3.jpg",
        "dataset/12_4.jpg",
    ]

    total_time = 0
    successful = 0
    detailed_records = []

    for idx, fpath in enumerate(test_files, 1):
        p = Path(fpath)
        if not p.exists():
            continue
        log(f"\n[{idx}/{len(test_files)}] Processing: {p.name}")
        log("-" * 60)
        try:
            t0 = time.time()
            img = prepare(str(p))
            t_pre = time.time() - t0

            t0 = time.time()
            raw = extract(img)
            t_ext = time.time() - t0

            t0 = time.time()
            marksheet, warnings = validate(raw)
            t_val = time.time() - t0

            step_time = t_pre + t_ext + t_val
            total_time += step_time
            successful += 1

            s_info = marksheet.student_info
            res = marksheet.result

            log(f"  • Board Name    : {marksheet.board or 'N/A'}")
            log(f"  • Examination   : {marksheet.examination or 'N/A'}")
            log(f"  • Student Name  : {s_info.name or 'N/A'}")
            log(f"  • Roll Number   : {s_info.roll_no or 'N/A'}")
            log(f"  • School/Inst   : {s_info.school_name or 'N/A'}")
            log(f"  • Result Status : {res.status or 'N/A'} (Percentage/Total: {res.percentage or res.total_obtained or 'N/A'})")
            log(f"  • Subjects ({len(marksheet.subjects)}):")
            for s in marksheet.subjects:
                th = f"Th:{s.theory}" if s.theory is not None else ""
                pr = f"Pr:{s.practical}" if s.practical is not None else ""
                tot = f"Tot:{s.total}" if s.total is not None else ""
                gr = f"Grd:{s.grade}" if s.grade else ""
                marks_str = " | ".join(filter(None, [th, pr, tot, gr]))
                log(f"      - {s.name:<30} : {marks_str}")
            
            if warnings:
                log(f"  • Arithmetic Warnings: {warnings}")
            else:
                log(f"  • Arithmetic Validation : PASSED (No discrepancies)")

            log(f"  • Timing        : Prep: {t_pre:.2f}s | VLM: {t_ext:.2f}s | Val: {t_val:.2f}s | Total: {step_time:.2f}s")
            
            detailed_records.append({
                "file": p.name,
                "board": marksheet.board,
                "student": s_info.name,
                "subjects": len(marksheet.subjects),
                "status": res.status,
                "time": round(step_time, 2)
            })

        except Exception as e:
            log(f"  [ERROR] Extraction failed for {p.name}: {e}")

    log()
    log("=" * 80)
    log("                             BENCHMARK SUMMARY")
    log("=" * 80)
    log(f"Total Processed Marksheets : {len(test_files)}")
    log(f"Successful Extractions     : {successful}/{len(test_files)} ({(successful/len(test_files))*100:.1f}%)")
    if successful > 0:
        log(f"Average Time Per Document  : {total_time/successful:.2f}s")
    log(f"Total Test Duration        : {total_time:.2f}s")
    log()
    log(f"{'Filename':<15} | {'Board':<30} | {'Candidate':<20} | {'Subjects':<8} | {'Status':<6} | {'Time'}")
    log("-" * 95)
    for r in detailed_records:
        b_str = (r['board'] or 'Unknown')[:28]
        c_str = (r['student'] or 'Unknown')[:18]
        log(f"{r['file']:<15} | {b_str:<30} | {c_str:<20} | {r['subjects']:<8} | {r['status'] or 'N/A':<6} | {r['time']}s")
    log("=" * 80)

    # Save to result.txt
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")
    print("\n[SUCCESS] Benchmark results saved to result.txt")

if __name__ == "__main__":
    run_all_tests()
