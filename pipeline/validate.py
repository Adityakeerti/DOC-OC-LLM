"""
validate.py — Validate and clean marksheet data from the VLM.

Uses Pydantic for type-safe schemas and adds arithmetic sanity checks
(theory + practical should equal total marks).

This catches VLM mistakes before the data reaches the user.
"""

import re
from typing import Optional
from pydantic import BaseModel, field_validator


# ── Coercion Helper ───────────────────────────────────────────────────────────

def _clean_numeric(v) -> Optional[float]:
    """Safely convert strings like '077', '97.0', '95', or '-' into floats or None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in ["", "-", "–", "—", "null", "None", "N/A", "NA", "AB", "ABSENT"]:
        return None
    # If a fraction like "450/500", extract numerator
    if "/" in s:
        s = s.split("/")[0]
    cleaned = re.sub(r"[^0-9.]", "", s)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


# ── Schema Models ─────────────────────────────────────────────────────────────

class Subject(BaseModel):
    """One subject row from the marksheet."""
    name: str = ""
    theory: Optional[float] = None
    practical: Optional[float] = None
    total: Optional[float] = None
    max_marks: Optional[float] = None
    grade: Optional[str] = None

    @field_validator("theory", "practical", "total", "max_marks", mode="before")
    @classmethod
    def coerce_marks(cls, v):
        return _clean_numeric(v)


class StudentInfo(BaseModel):
    """Student details from the top section of the marksheet."""
    name: Optional[str] = None
    roll_no: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    school_name: Optional[str] = None
    dob: Optional[str] = None

    @field_validator("name", "father_name", "mother_name", mode="before")
    @classmethod
    def clean_name_prefixes(cls, v):
        if not v or not isinstance(v, str):
            return v
        s = v.strip()
        s = re.sub(r"^(Mr\.?|Mrs\.?|Smt\.?|Shri\.?|Master\.?|Km\.?|Miss\.?)\s+", "", s, flags=re.IGNORECASE).strip()
        return s


class Result(BaseModel):
    """Overall result summary from the bottom of the marksheet."""
    total_obtained: Optional[float] = None
    maximum_marks: Optional[float] = None
    percentage: Optional[str] = None
    status: Optional[str] = None

    @field_validator("total_obtained", "maximum_marks", mode="before")
    @classmethod
    def coerce_result_marks(cls, v):
        return _clean_numeric(v)

    @field_validator("percentage", mode="before")
    @classmethod
    def coerce_percentage(cls, v):
        if not v:
            return None
        s = str(v).strip()
        if "/" in s:
            parts = s.split("/")
            try:
                num = _clean_numeric(parts[0])
                den = _clean_numeric(parts[1])
                if num is not None and den is not None and den > 0:
                    return f"{round((num / den) * 100, 2)}%"
            except Exception:
                pass
        return s

    @field_validator("status")
    @classmethod
    def normalize_status(cls, v):
        """Standardize status to PASS / FAIL / COMPARTMENT."""
        if not v:
            return v
        v = v.strip().upper()
        if "PASS" in v:
            return "PASS"
        if "FAIL" in v:
            return "FAIL"
        if "COMP" in v:
            return "COMPARTMENT"
        return v


class Marksheet(BaseModel):
    """Complete marksheet extraction — the final output schema."""
    board: Optional[str] = None
    examination: Optional[str] = None
    student_info: StudentInfo = StudentInfo()
    subjects: list[Subject] = []
    result: Result = Result()


# ── ICSE Sub-Paper & Grade Reconciliation ──────────────────────────────────

ICSE_DIGIT_WORDS = {
    "ZERO": 0, "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4,
    "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9
}

def parse_icse_grade_marks(grade_str: Optional[str]) -> Optional[float]:
    """Parse ICSE percentage words from grade column (e.g. 'EIGHT SIX' -> 86.0, 'NINE ONE' -> 91.0)."""
    if not grade_str:
        return None
    tokens = [w for w in grade_str.upper().split() if w in ICSE_DIGIT_WORDS]
    if len(tokens) == 2:
        return float(ICSE_DIGIT_WORDS[tokens[0]] * 10 + ICSE_DIGIT_WORDS[tokens[1]])
    return None

def reconcile_icse_subjects(marksheet: Marksheet) -> list[str]:
    """
    In ICSE (CISCE) marksheets, parent subjects (ENGLISH; HISTORY, CIVICS & GEOGRAPHY; SCIENCE)
    are often followed by indented sub-papers (ENGLISH LANGUAGE, LITERATURE IN ENGLISH,
    HISTORY & CIVICS, GEOGRAPHY, PHYSICS, CHEMISTRY, BIOLOGY).
    
    If sub-papers are extracted alongside parent subjects, roll up the sub-paper marks
    into the parent subjects (using ICSE official averaging rules) and prune the sub-papers.
    Also grounds parent subject marks to the printed word grade (e.g. 'EIGHT SIX' -> 86.0).
    """
    warnings = []
    board_text = ((marksheet.board or "") + " " + (marksheet.examination or "")).upper()
    is_class_12 = any(k in board_text for k in [
        "CLASS - XII", "CLASS-XII", "CLASS XII", "CLASS 12", "CLASS-12",
        "ISC", "INTERMEDIATE", "SENIOR SECONDARY", "SENIOR SCHOOL", "HSC", "12TH"
    ])

    # In Class 12 / Intermediate, Physics, Chemistry, and Biology are distinct academic subjects,
    # NEVER component sub-papers of Science!
    ICSE_SUB_PAPERS = {
        "ENGLISH LANGUAGE": "ENGLISH",
        "LITERATURE IN ENGLISH": "ENGLISH",
        "HISTORY & CIVICS": "HISTORY, CIVICS & GEOGRAPHY",
        "GEOGRAPHY": "HISTORY, CIVICS & GEOGRAPHY",
    }
    if not is_class_12:
        ICSE_SUB_PAPERS["PHYSICS"] = "SCIENCE"
        ICSE_SUB_PAPERS["CHEMISTRY"] = "SCIENCE"
        ICSE_SUB_PAPERS["BIOLOGY"] = "SCIENCE"

    is_icse = any(k in board_text for k in [
        "COUNCIL FOR THE INDIAN SCHOOL", "ICSE", "CISCE",
        "INDIAN CERTIFICATE OF SECONDARY EDUCATION", "INDIAN SCHOOL CERTIFICATE"
    ])

    subj_names_upper = {s.name.strip().upper(): s for s in marksheet.subjects}
    found_sub_papers = [name for name in subj_names_upper if name in ICSE_SUB_PAPERS]

    has_parent_overlap = any(
        ICSE_SUB_PAPERS[sp] in subj_names_upper for sp in found_sub_papers
    )

    if not (is_icse or (found_sub_papers and has_parent_overlap)):
        return warnings

    parent_sub_marks: dict[str, list[Subject]] = {}
    for sp_name in found_sub_papers:
        parent = ICSE_SUB_PAPERS[sp_name]
        parent_sub_marks.setdefault(parent, []).append(subj_names_upper[sp_name])

    cleaned_subjects: list[Subject] = []
    seen_parents = set()

    for s in marksheet.subjects:
        name_upper = s.name.strip().upper()
        if name_upper in ICSE_SUB_PAPERS:
            warnings.append(f"ICSE Layout: Pruned component paper '{s.name}' into parent '{ICSE_SUB_PAPERS[name_upper]}'")
            continue

        grade_val = parse_icse_grade_marks(s.grade)

        if name_upper in parent_sub_marks:
            seen_parents.add(name_upper)
            sub_list = parent_sub_marks[name_upper]
            # Sanitize sub-totals to prevent unpruned sum overflow
            sub_totals = []
            for sub in sub_list:
                val = sub.total if (sub.total is not None and sub.total <= 100.0) else sub.theory
                if val is not None and val <= 100.0:
                    sub_totals.append(val)

            avg_total = float(round(sum(sub_totals) / len(sub_totals))) if sub_totals else None

            # Prioritize official word grade if present, else computed average
            target_mark = grade_val if grade_val is not None else avg_total
            if target_mark is not None:
                old_tot = s.total
                s.total = target_mark
                s.theory = target_mark
                s.practical = None
                warnings.append(
                    f"ICSE Layout: Reconciled parent subject '{s.name}' total to {target_mark} "
                    f"(from {'word grade ' + s.grade if grade_val else 'component papers average ' + str(sub_totals)}, was {old_tot})"
                )
        else:
            # Standalone ICSE subject (HINDI, MATHEMATICS, PHYSICAL EDUCATION, COMPUTER APPLICATIONS)
            if grade_val is not None and (s.total is None or s.total > 100.0 or abs(s.total - grade_val) > 3):
                s.total = grade_val
                s.theory = grade_val
                s.practical = None
                warnings.append(f"ICSE Layout: Grounded '{s.name}' total to {grade_val} from word grade '{s.grade}'")

        if s.total is not None and s.total > 100.0:
            if grade_val is not None:
                s.total = grade_val
                s.theory = grade_val
            elif s.theory is not None and s.theory <= 100.0:
                s.total = s.theory

        cleaned_subjects.append(s)

    # If a parent subject was missing from the extraction but its sub-papers were extracted:
    for parent, sub_list in parent_sub_marks.items():
        if parent not in seen_parents:
            sub_totals = [sub.total for sub in sub_list if sub.total is not None and sub.total <= 100.0]
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


# ── Arithmetic Checks ─────────────────────────────────────────────────────────

def check_arithmetic(marksheet: Marksheet) -> list[str]:
    """
    Verify that theory + practical = total for each subject.
    Filters out bogus header rows and auto-reconciles missing practical/IA marks.
    """
    warnings = []

    # 1. Filter out category/header rows that are not subjects
    BOGUS_LABELS = [
        "ADDITIONAL SUBJECT", "ADDITIONAL", "COMPULSORY", "ELECTIVE",
        "INTERNAL ASSESSMENT", "SUPW", "OVERALL RESULT", "RESULT",
        "WORK EXPERIENCE", "HEALTH & PHYSICAL EDUCATION", "GENERAL STUDIES",
        "PHYSICAL & HEALTH EDUCATION", "HEALTH & PHYSICAL", "GENERAL AWARENESS"
    ]
    cleaned_subjects = []
    for s in marksheet.subjects:
        norm_name = s.name.strip().upper()
        if any(norm_name == b or norm_name.startswith(b + " ") for b in BOGUS_LABELS):
            warnings.append(f"Filtered out non-academic/co-scholastic row: '{s.name}'")
            continue
        # Also skip rows with no numeric marks at all (grading-only co-scholastic rows)
        if s.theory is None and s.practical is None and s.total is None:
            warnings.append(f"Filtered out grading-only row: '{s.name}'")
            continue
        cleaned_subjects.append(s)
    marksheet.subjects = cleaned_subjects

    # 2. Arithmetic reconciliation
    for subj in marksheet.subjects:
        # If total is missing but theory is present and practical is None:
        if subj.total is None and subj.theory is not None and subj.practical is None:
            subj.total = subj.theory
            warnings.append(f"{subj.name}: Auto-set Total to Theory ({subj.theory})")
        # Conversely, if theory is missing but total is present and practical is None:
        elif subj.theory is None and subj.total is not None and subj.practical is None:
            subj.theory = subj.total

        # If total is present and theory is present, but practical is missing:
        if subj.total is not None and subj.theory is not None:
            diff = round(subj.total - subj.theory, 2)
            if subj.practical is None and 0 < diff <= 75:
                subj.practical = diff
                warnings.append(
                    f"{subj.name}: Auto-reconciled practical/internal assessment to {diff} "
                    f"(Total {subj.total} - Theory {subj.theory})"
                )

        # 2a. Self-healing: if theory equals total, practical was blank/zero
        if subj.theory is not None and subj.total is not None and subj.theory == subj.total and subj.practical is not None:
            subj.practical = None
            warnings.append(f"{subj.name}: Practical reset to null because Theory equals Total ({subj.total})")

        # 2b. Self-healing: if practical was duplicated from theory (e.g. Theory 80, Practical 80 -> Total 160)
        if subj.practical is not None and subj.theory is not None and subj.practical == subj.theory:
            if subj.total is None or subj.total > (subj.max_marks or 100.0):
                subj.practical = None
                subj.total = subj.theory
                warnings.append(f"{subj.name}: Reset duplicated practical to null (Total set to {subj.theory})")

        # 2c. Self-healing: subject total cannot exceed max marks
        max_limit = subj.max_marks or 100.0
        if subj.total is not None and subj.total > max_limit:
            if subj.theory is not None and subj.theory <= max_limit:
                subj.total = subj.theory
                subj.practical = None
                warnings.append(f"{subj.name}: Total exceeded {max_limit}; reset to Theory {subj.theory}")

        # 2d. Self-healing: Practical in a standard 100-mark paper cannot exceed 75
        # Exception: Valid subjects like Painting/Music/IT/Computer Applications have Practical up to 70
        if subj.practical is not None and subj.practical > 75.0 and max_limit <= 100.0:
            if subj.theory is not None and subj.total is not None and abs(subj.theory + subj.practical - subj.total) <= 1:
                pass  # Valid high-practical subject (e.g. Painting: Theory 27 + Practical 70 = Total 97)
            else:
                candidate_total = subj.practical
                subj.practical = None
                if subj.total is None or subj.total > max_limit or abs(subj.total - candidate_total) > 5:
                    subj.total = candidate_total
                if subj.theory is not None and subj.theory < subj.total:
                    diff = round(subj.total - subj.theory, 2)
                    if 0 < diff <= 75:
                        subj.practical = diff
                warnings.append(f"{subj.name}: Corrected misaligned practical {candidate_total} into Total {subj.total}")

        # 2e. Self-healing: Theory + Practical cannot exceed max marks (e.g. 89 + 20 = 109 > 100)
        if subj.theory is not None and subj.practical is not None:
            if (subj.theory + subj.practical) > max_limit:
                old_prac = subj.practical
                subj.practical = None
                subj.total = subj.theory
                warnings.append(
                    f"{subj.name}: Practical reset to null because Theory ({subj.theory}) + "
                    f"Practical ({old_prac}) exceeds max marks {max_limit}"
                )

        if subj.theory is None or subj.practical is None or subj.total is None:
            continue

        expected = subj.theory + subj.practical

        if abs(expected - subj.total) > 1:
            # If model mistook maximum marks (e.g. 100) as total obtained
            if subj.total in [100.0, 50.0, 75.0, 200.0] and expected < subj.total:
                old_total = subj.total
                if subj.max_marks is None:
                    subj.max_marks = old_total
                subj.total = expected
                warnings.append(
                    f"{subj.name}: Auto-reconciled total marks obtained to {expected} "
                    f"({subj.theory} + {subj.practical}), max marks set to {old_total}"
                )
            elif abs(expected - subj.total) <= 3 and expected <= (subj.max_marks or 100.0):
                # Minor OCR digit confusion (e.g. '98' instead of '96' when Theory=76, Practical=20)
                old_total = subj.total
                subj.total = expected
                warnings.append(
                    f"{subj.name}: Corrected OCR total digit slip from {old_total} to {expected} "
                    f"({subj.theory} + {subj.practical})"
                )
            else:
                warnings.append(
                    f"{subj.name}: {subj.theory} + {subj.practical} = {expected}, "
                    f"but total shows {subj.total}"
                )

    # 3. Detect duplicate parents (Mother == Father slip)
    if marksheet.student_info.mother_name and marksheet.student_info.father_name:
        if marksheet.student_info.mother_name.strip().upper() == marksheet.student_info.father_name.strip().upper():
            warnings.append(
                f"Candidate parents conflict: Mother and Father have identical name '{marksheet.student_info.mother_name}'."
            )

    return warnings


def reconcile_aggregate_results(marksheet: Marksheet) -> list[str]:
    """
    If total_obtained, maximum_marks, or percentage are missing or partial,
    reconcile them automatically from the validated subject list.
    """
    warnings = []
    academic_subjs = [
        s for s in marksheet.subjects
        if s.total is not None and s.total > 0
        and "INTERNAL ASSESSMENT" not in s.name.upper()
        and "SUPW" not in s.name.upper()
    ]

    if not academic_subjs:
        return warnings

    sum_obtained = sum(s.total for s in academic_subjs)
    sum_max = sum(s.max_marks or 100.0 for s in academic_subjs)

    # 1. Total obtained reconciliation
    curr_total = marksheet.result.total_obtained
    if curr_total is None or curr_total > sum_max or (curr_total < sum_obtained * 0.4 and len(academic_subjs) >= 3):
        marksheet.result.total_obtained = sum_obtained
        warnings.append(
            f"Auto-reconciled grand total obtained to {sum_obtained} from {len(academic_subjs)} academic subjects"
        )
    elif curr_total is not None and abs(curr_total - sum_obtained) <= 5 and sum_obtained > 0:
        if curr_total != sum_obtained:
            warnings.append(
                f"Corrected result grand total from {curr_total} to verified subject sum {sum_obtained}"
            )
            marksheet.result.total_obtained = sum_obtained

    # 2. Maximum marks reconciliation (cap inflated maximum_marks from co-scholastic rows)
    if marksheet.result.maximum_marks is None or marksheet.result.maximum_marks > sum_max or marksheet.result.maximum_marks < marksheet.result.total_obtained:
        marksheet.result.maximum_marks = sum_max

    # 3. Percentage reconciliation
    if marksheet.result.maximum_marks and marksheet.result.total_obtained:
        pct = round((marksheet.result.total_obtained / marksheet.result.maximum_marks) * 100, 2)
        marksheet.result.percentage = f"{pct}%"

    return warnings


# ── Main Validation ───────────────────────────────────────────────────────────

def validate(raw_data: dict) -> tuple[Marksheet, list[str]]:
    """
    Validate raw VLM output and return a clean Marksheet + warnings.

    Args:
        raw_data: dict from the VLM's JSON response

    Returns:
        (marksheet, warnings) — validated Pydantic model + any issues found
    """
    # Pydantic handles type coercion, missing fields, and structure validation
    marksheet = Marksheet.model_validate(raw_data)

    # Step 1: Reconcile ICSE component sub-papers into aggregate subjects
    icse_warnings = reconcile_icse_subjects(marksheet)

    # Step 2: Run arithmetic sanity checks
    warnings = icse_warnings + check_arithmetic(marksheet)

    # Step 3: Reconcile grand total & percentage if missing or partial
    agg_warnings = reconcile_aggregate_results(marksheet)
    warnings.extend(agg_warnings)

    return marksheet, warnings
