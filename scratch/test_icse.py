import json
from scratch.inspect_runs import parsed_runs

ICSE_SUB_PAPERS = {
    "ENGLISH LANGUAGE": "ENGLISH",
    "LITERATURE IN ENGLISH": "ENGLISH",
    "HISTORY & CIVICS": "HISTORY, CIVICS & GEOGRAPHY",
    "GEOGRAPHY": "HISTORY, CIVICS & GEOGRAPHY",
    "PHYSICS": "SCIENCE",
    "CHEMISTRY": "SCIENCE",
    "BIOLOGY": "SCIENCE"
}

def test_icse_reconciliation(raw_json):
    subjects = raw_json.get("subjects", [])
    subj_map = {s["name"].strip().upper(): s for s in subjects}
    
    # Check if this document has ICSE sub-papers
    found_sub_papers = [name for name in subj_map if name in ICSE_SUB_PAPERS]
    print(f"Found sub-papers: {found_sub_papers}")
    
    if not found_sub_papers:
        return subjects
        
    # Group sub-paper marks by parent
    parent_sub_marks = {}
    for sp_name in found_sub_papers:
        parent = ICSE_SUB_PAPERS[sp_name]
        parent_sub_marks.setdefault(parent, []).append(subj_map[sp_name])
        
    # Reconcile parent marks
    cleaned_subjects = []
    seen_parents = set()
    
    for s in subjects:
        name_upper = s["name"].strip().upper()
        if name_upper in ICSE_SUB_PAPERS:
            # Skip sub-papers from final list
            continue
            
        if name_upper in parent_sub_marks:
            seen_parents.add(name_upper)
            # Reconcile from sub-papers
            sub_list = parent_sub_marks[name_upper]
            sub_totals = [sub.get("total") for sub in sub_list if sub.get("total") is not None]
            if sub_totals:
                avg_total = round(sum(sub_totals) / len(sub_totals))
                s["total"] = float(avg_total)
                s["theory"] = float(avg_total)
                s["practical"] = None
        cleaned_subjects.append(s)
        
    # If a parent subject was missing from subjects list but its sub-papers existed:
    for parent, sub_list in parent_sub_marks.items():
        if parent not in seen_parents:
            sub_totals = [sub.get("total") for sub in sub_list if sub.get("total") is not None]
            if sub_totals:
                avg_total = round(sum(sub_totals) / len(sub_totals))
                cleaned_subjects.append({
                    "name": parent,
                    "theory": float(avg_total),
                    "practical": None,
                    "total": float(avg_total),
                    "max_marks": 100.0,
                    "grade": None
                })
                
    return cleaned_subjects

print("=== RUN-18 (10_1.pdf) ===")
res18 = test_icse_reconciliation(parsed_runs[18]["json"])
for s in res18:
    print(f"  {s['name']}: {s.get('total')}")
tot18 = sum(s.get('total') for s in res18 if s.get('total'))
print(f"Total: {tot18} / {len(res18)*100} ({round(tot18/(len(res18)*100)*100, 2)}%)")

print("\n=== RUN-27 (10_13.jpg) ===")
res27 = test_icse_reconciliation(parsed_runs[27]["json"])
for s in res27:
    print(f"  {s['name']}: {s.get('total')}")
tot27 = sum(s.get('total') for s in res27 if s.get('total'))
print(f"Total: {tot27} / {len(res27)*100} ({round(tot27/(len(res27)*100)*100, 2)}%)")
