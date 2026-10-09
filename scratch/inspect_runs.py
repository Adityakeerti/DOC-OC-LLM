import re
import json
from pathlib import Path

content = Path("log.txt").read_text(encoding="utf-8")
blocks = content.split("================================================================================")

parsed_runs = {}
for block in blocks:
    m = re.search(r"RUN-(\d+) - (.*?)\nFile: (.*?)\n", block)
    if not m:
        continue
    run_no = int(m.group(1))
    if run_no < 18:
        continue
    filename = m.group(3).strip()
    
    warn_m = re.search(r"Warnings: (\[.*?\])\n", block)
    timing_m = re.search(r"Timing: (.*?)\n", block)
    
    # find json
    j_idx = block.find("JSON:\n")
    js = {}
    if j_idx != -1:
        json_str = block[j_idx + 6:].strip()
        brace_start = json_str.find("{")
        if brace_start != -1:
            depth = 0
            brace_end = -1
            for i, c in enumerate(json_str[brace_start:]):
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        brace_end = brace_start + i + 1
                        break
            if brace_end != -1:
                try:
                    js = json.loads(json_str[brace_start:brace_end])
                except Exception as ex:
                    print(f"Error parsing JSON in RUN-{run_no}: {ex}")
    
    warns = json.loads(warn_m.group(1)) if warn_m else []
    timing = timing_m.group(1) if timing_m else ""
    parsed_runs[run_no] = {
        "file": filename,
        "timing": timing,
        "warnings": warns,
        "json": js
    }

print("Total runs >= 18 parsed:", len(parsed_runs))
for rno, rdata in sorted(parsed_runs.items()):
    js = rdata["json"]
    sinfo = js.get("student_info", {})
    subjs = js.get("subjects", [])
    res = js.get("result", {})
    fname = rdata["file"]
    print(f"\n==================== RUN-{rno}: {fname} ====================")
    c_name = sinfo.get('name')
    r_no = sinfo.get('roll_no')
    m_name = sinfo.get('mother_name')
    f_name = sinfo.get('father_name')
    dob = sinfo.get('dob')
    school = sinfo.get('school_name')
    print(f"Candidate: {c_name} | Roll: {r_no} | Mother: {m_name} | Father: {f_name}")
    print(f"DOB: {dob} | School: {school}")
    print(f"Subjects ({len(subjs)}):")
    for s in subjs:
        sname = s.get('name')
        th = s.get('theory')
        pr = s.get('practical')
        tot = s.get('total')
        mx = s.get('max_marks')
        gr = s.get('grade')
        print(f"  - {sname}: th={th}, pr={pr}, tot={tot}, max={mx}, gr={gr}")
    t_obt = res.get('total_obtained')
    m_obt = res.get('maximum_marks')
    pct = res.get('percentage')
    st = res.get('status')
    print(f"Result: total={t_obt}/{m_obt}, pct={pct}, status={st}")
    if rdata["warnings"]:
        print("Warnings:", rdata["warnings"])
