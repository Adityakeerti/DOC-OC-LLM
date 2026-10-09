"""
test_10_boards.py — Benchmark and deep-audit DOC-OC v6 across 10 diverse Indian board marksheets.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.preprocess import prepare
from pipeline.extract import extract
from pipeline.validate import validate

TEST_FILES = [
    {
        "id": "1. Karnataka SSLC",
        "path": "/home/aditya/Desktop/Screenshot_20261010_025033.png",
        "board": "Karnataka Secondary Education Examination Board (SSLC)"
    },
    {
        "id": "2. ICSE Class 10",
        "path": "dataset/10_1.jpg",
        "board": "Council for the Indian School Certificate Examinations (ICSE 10th)"
    },
    {
        "id": "3. ISC Class 12",
        "path": "dataset/12_1.jpg",
        "board": "Council for the Indian School Certificate Examinations (ISC 12th)"
    },
    {
        "id": "4. CBSE Class 10",
        "path": "dataset/10_3.jpg",
        "board": "Central Board of Secondary Education (CBSE 10th)"
    },
    {
        "id": "5. CBSE Class 12",
        "path": "dataset/12_3.jpg",
        "board": "Central Board of Secondary Education (CBSE 12th)"
    },
    {
        "id": "6. Uttarakhand 10th",
        "path": "dataset/10_2.jpg",
        "board": "Uttarakhand Board of School Education (UBSE 10th)"
    },
    {
        "id": "7. Uttarakhand 12th",
        "path": "dataset/12_4.jpg",
        "board": "Uttarakhand Board of School Education (UBSE 12th)"
    },
    {
        "id": "8. Haryana 10th",
        "path": "dataset/haryana_10th.png",
        "board": "Board of School Education Haryana (BSEH 10th)"
    },
    {
        "id": "9. Haryana 12th",
        "path": "dataset/haryana_12th.png",
        "board": "Board of School Education Haryana (BSEH 12th)"
    },
    {
        "id": "10. UP Board 10th",
        "path": "dataset/up_board_10th.png",
        "board": "Board of High School & Intermediate Education UP (UPMSP 10th)"
    },
]

def run_benchmark():
    print("=" * 80)
    print("DOC-OC v6 — Universal 10-Board Deep Audit Benchmark")
    print("=" * 80)

    results = []

    for item in TEST_FILES:
        name = item["id"]
        filepath = item["path"]
        board_label = item["board"]

        print(f"\n[{name}] Testing: {filepath}")
        if not os.path.exists(filepath):
            print(f"  ❌ File not found: {filepath}")
            results.append({"name": name, "status": "FILE_NOT_FOUND"})
            continue

        t0 = time.time()
        try:
            # 1. Preprocess
            t_pre_start = time.time()
            img = prepare(filepath)
            t_pre = round(time.time() - t_pre_start, 2)

            # 2. Extract
            t_ext_start = time.time()
            raw = extract(img)
            t_ext = round(time.time() - t_ext_start, 2)

            # 3. Validate
            t_val_start = time.time()
            validated, warnings = validate(raw)
            t_val = round(time.time() - t_val_start, 3)

            total_time = round(time.time() - t0, 2)

            res_dict = validated.model_dump()
            student = res_dict["student_info"]
            subjects = res_dict["subjects"]
            result = res_dict["result"]

            print(f"  ⚡ Latency: {total_time}s (Pre: {t_pre}s | VLM: {t_ext}s | Val: {t_val}s)")
            print(f"  📋 Board: {res_dict.get('board')}")
            print(f"  👤 Candidate: '{student.get('name')}' | Roll: '{student.get('roll_no')}'")
            print(f"  👪 Parents: Mother='{student.get('mother_name')}', Father='{student.get('father_name')}'")
            print(f"  🏫 School: '{student.get('school_name')}'")
            print(f"  📚 Subjects ({len(subjects)}):")
            for s in subjects:
                th_str = f"Th:{s['theory']}" if s['theory'] is not None else ""
                pr_str = f"Pr:{s['practical']}" if s['practical'] is not None else ""
                breakdown = f" ({th_str} {pr_str})".replace(" ()", "")
                print(f"     • {s['name']:<28} Total: {s['total']:<5} Max: {s['max_marks']:<5} Grade: {s['grade'] or '-'}{breakdown}")
            print(f"  🏆 Overall Result: {result.get('total_obtained')} / {result.get('maximum_marks')} ({result.get('percentage')}) Status: {result.get('status')}")
            if warnings:
                print(f"  ⚠️ Warnings: {warnings}")

            results.append({
                "name": name,
                "status": "SUCCESS",
                "time": total_time,
                "data": res_dict,
                "warnings": warnings
            })

        except Exception as e:
            print(f"  ❌ FAILED with error: {e}")
            results.append({
                "name": name,
                "status": "ERROR",
                "error": str(e)
            })

    print("\n" + "=" * 80)
    print("AUDIT SUMMARY:")
    print("=" * 80)
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    print(f"Total Tested: {len(results)} | Succeeded: {success_count}/{len(results)}")
    for r in results:
        status_symbol = "✅" if r["status"] == "SUCCESS" else "❌"
        t_str = f"({r.get('time', 0)}s)" if "time" in r else ""
        print(f"  {status_symbol} {r['name']:<25} {t_str}")

if __name__ == "__main__":
    run_benchmark()
