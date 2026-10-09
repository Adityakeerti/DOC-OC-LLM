import json
import re
from typing import Optional
from pydantic import BaseModel, field_validator

# Import the existing validate models or replicate for quick test
from pipeline.validate import Marksheet, Subject, StudentInfo, Result, check_arithmetic, reconcile_aggregate_results, validate
from scratch.inspect_runs import parsed_runs

def test_on_runs():
    print("Testing fixes against parsed runs 18 to 27...")
    for rno, rdata in sorted(parsed_runs.items()):
        raw_json = rdata["json"]
        m, warns = validate(raw_json)
        print(f"\n--- RUN-{rno}: {rdata['file']} ---")
        print(f"Cand: {m.student_info.name} | M: {m.student_info.mother_name} | F: {m.student_info.father_name}")
        print(f"Subjects ({len(m.subjects)}): {[s.name for s in m.subjects]}")
        print(f"Result: {m.result.total_obtained}/{m.result.maximum_marks} ({m.result.percentage})")

test_on_runs()
