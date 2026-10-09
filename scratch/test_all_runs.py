from pipeline.validate import Marksheet, Subject, StudentInfo, Result
import re
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

def reconcile_icse_subjects(marksheet: Marksheet) -> list[str]:
    warnings = []
    board_text = ((marksheet.board or "") + " " + (marksheet.examination or "")).upper()
    is_icse = any(k in board_text for k in ["COUNCIL FOR THE INDIAN SCHOOL", "ICSE", "CISCE", "INDIAN CERTIFICATE OF SECONDARY EDUCATION"])

    subj_names_upper = {s.name.strip().upper(): s for s in marksheet.subjects}
    found_sub_papers = [name for name in subj_names_upper if name in ICSE_SUB_PAPERS]

    has_parent_overlap = any(
        ICSE_SUB_PAPERS[sp] in subj_names_upper for sp in found_sub_papers
    )

    if not (is_icse or (found_sub_papers and has_parent_overlap)):
        return warnings

    parent_sub_marks = {}
    for sp_name in found_sub_papers:
        parent = ICSE_SUB_PAPERS[sp_name]
        parent_sub_marks.setdefault(parent, []).append(subj_names_upper[sp_name])

    cleaned_subjects = []
    seen_parents = set()

    for s in marksheet.subjects:
        name_upper = s.name.strip().upper()
        if name_upper in ICSE_SUB_PAPERS:
            warnings.append(f"ICSE Layout: Pruned component paper '{s.name}' into parent '{ICSE_SUB_PAPERS[name_upper]}'")
            continue

        if name_upper in parent_sub_marks:
            seen_parents.add(name_upper)
            sub_list = parent_sub_marks[name_upper]
            sub_totals = [sub.total for sub in sub_list if sub.total is not None]
            if sub_totals:
                avg_total = float(round(sum(sub_totals) / len(sub_totals)))
                if s.total is None or abs(s.total - avg_total) > 0:
                    old_tot = s.total
                    s.total = avg_total
                    s.theory = avg_total
                    s.practical = None
                    warnings.append(
                        f"ICSE Layout: Reconciled parent subject '{s.name}' total to {avg_total} "
                        f"(average of component papers: {sub_totals}, was {old_tot})"
                    )
        cleaned_subjects.append(s)

    for parent, sub_list in parent_sub_marks.items():
        if parent not in seen_parents:
            sub_totals = [sub.total for sub in sub_list if sub.total is not None]
            if sub_totals:
                avg_total = float(round(sum(sub_totals) / len(sub_totals)))
                cleaned_subjects.append(Subject(
                    name=parent,
                    theory=avg_total,
                    practical=None,
                    total=avg_total,
                    max_marks=100.0,
                    grade=None
                ))
                warnings.append(
                    f"ICSE Layout: Synthesized parent subject '{parent}' with total {avg_total} "
                    f"from component papers {sub_totals}"
                )

    marksheet.subjects = cleaned_subjects
    return warnings

from pipeline.validate import check_arithmetic, reconcile_aggregate_results

for rno, rdata in sorted(parsed_runs.items()):
    m = Marksheet.model_validate(rdata["json"])
    w1 = reconcile_icse_subjects(m)
    w2 = check_arithmetic(m)
    w3 = reconcile_aggregate_results(m)
    print(f"\n=== RUN-{rno}: {rdata['file']} ===")
    print(f"Subjects ({len(m.subjects)}):")
    for s in m.subjects:
        print(f"  {s.name}: th={s.theory}, pr={s.practical}, tot={s.total}")
    print(f"Result: {m.result.total_obtained}/{m.result.maximum_marks} ({m.result.percentage})")
    all_w = w1 + w2 + w3
    if all_w:
        print(f"Warnings ({len(all_w)}): {all_w[:3]}")
