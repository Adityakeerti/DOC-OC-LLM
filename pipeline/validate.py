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

def reconcile_board_identity(marksheet: Marksheet) -> list[str]:
    """Correct board identity if header crest/location clearly indicates a specific state board."""
    warnings = []
    all_text = " ".join(filter(None, [
        marksheet.board,
        marksheet.examination,
        marksheet.student_info.school_name,
        marksheet.student_info.name
    ])).upper()
    
    # 1. UP Board
    if any(k in all_text for k in ["UTTAR PRADESH", "U.P. BOARD", "ALLAHABAD", "PRAYAGRAJ", "माध्यमिक शिक्षा परिषद्"]):
        if not marksheet.board or "UTTARAKHAND" in marksheet.board.upper() or "HARYANA" in marksheet.board.upper():
            marksheet.board = "Board of High School and Intermediate Education Uttar Pradesh"
            warnings.append("Grounded board identity to 'Board of High School and Intermediate Education Uttar Pradesh'")
        return warnings

    # 2. Uttarakhand Board
    if any(k in all_text for k in ["RAMNAGAR", "NAINITAL", "PITHORAGARH", "DEHRADUN", "HARIDWAR", "UTTARAKHAND", "UBSE"]):
        if marksheet.board and ("HARYANA" in marksheet.board.upper() or "UTTAR PRADESH" in marksheet.board.upper()):
            marksheet.board = "Board of School Education Uttarakhand"
            warnings.append("Corrected board identity to 'Board of School Education Uttarakhand' based on institutional location")
        return warnings

    # 3. Haryana Board
    if any(k in all_text for k in ["HARYANA", "BSEH", "BHIWANI", "GOHRAN", "KAITHAL", "ROHTAK"]):
        if marksheet.board and "UTTARAKHAND" in marksheet.board.upper():
            marksheet.board = "Board of School Education Haryana"
            warnings.append("Corrected board identity to 'Board of School Education Haryana'")
        return warnings

    # 4. Karnataka Board
    if any(k in all_text for k in ["KARNATAKA", "KSEEB", "K.S.E.E.B", "BANGALORE", "BENGALURU"]):
        marksheet.board = "Karnataka Secondary Education Examination Board"
        warnings.append("Grounded board identity to 'Karnataka Secondary Education Examination Board'")
        return warnings

    return warnings

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

        seen_parents.add(name_upper)
        grade_val = parse_icse_grade_marks(s.grade)

        if grade_val is not None:
            s.total = grade_val
            s.theory = grade_val
            s.practical = None
            warnings.append(f"ICSE Layout: Grounded '{s.name}' total to {grade_val} from word grade '{s.grade}'")
        elif s.total is not None and s.total <= 100.0:
            s.theory = s.total
            s.practical = None
        elif s.theory is not None and s.theory <= 100.0:
            s.total = s.theory
            s.practical = None
        elif name_upper in parent_sub_marks:
            sub_list = parent_sub_marks[name_upper]
            sub_totals = [sub.total for sub in sub_list if sub.total is not None and sub.total <= 100.0]
            if sub_totals:
                avg_total = float(round(sum(sub_totals) / len(sub_totals)))
                s.total = avg_total
                s.theory = avg_total
                s.practical = None
                warnings.append(
                    f"ICSE Layout: Reconciled parent subject '{s.name}' total to {avg_total} "
                    f"from component papers average {sub_totals}"
                )

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
                seen_parents.add(parent)
                warnings.append(
                    f"ICSE Layout: Synthesized parent subject '{parent}' with total {avg_total} "
                    f"from component papers {sub_totals}"
                )

    marksheet.subjects = cleaned_subjects
    return warnings


# ── Arithmetic Checks ─────────────────────────────────────────────────────────

def parse_numeric_grade(grade_str: Optional[str]) -> Optional[float]:
    """Extract numeric marks if grade column contains actual marks (e.g. '93', '118'), not letter grades ('A1', 'B')."""
    if not grade_str:
        return None
    s = str(grade_str).strip()
    # Letter grades or status words are not marks
    if re.match(r"^[A-Ga-gOoSs][1-9]?\+?$", s) or s.upper() in ["PASS", "FAIL", "DISTINCTION", "FIRST", "SECOND", "THIRD", "COMP", "QUALIFIED"]:
        return None
    cleaned = re.sub(r"[^0-9.]", "", s)
    try:
        val = float(cleaned) if cleaned else None
        if val is not None and val > 10.0:  # Valid marks obtained
            return val
    except ValueError:
        pass
    return None


def check_arithmetic(marksheet: Marksheet) -> list[str]:
    """
    Verify that theory + practical = total for each subject.
    Filters out bogus header rows and auto-reconciles missing practical/IA marks.
    """
    warnings = []
    board_text = ((marksheet.board or "") + " " + (marksheet.examination or "")).upper()
    is_icse = any(k in board_text for k in ["COUNCIL FOR THE INDIAN SCHOOL", "ICSE", "CISCE"])
    is_karnataka = "KARNATAKA" in board_text
    is_haryana = "HARYANA" in board_text

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
        # Skip rows with no numeric marks and no grade
        if s.theory is None and s.practical is None and s.total is None and not s.grade:
            warnings.append(f"Filtered out empty row: '{s.name}'")
            continue
        cleaned_subjects.append(s)
    marksheet.subjects = cleaned_subjects

    STANDARD_THEORY_SUBJS = [
        "ENGLISH", "ENGLISH CORE", "ENGLISH LNG & LIT", "ENGLISH COMM.", "ENGLISH ELECTIVE",
        "HINDI", "HINDI COURSE-A", "HINDI COURSE-B", "HINDI CORE", "HINDI ELECTIVE",
        "MATHEMATICS", "MATHEMATICS STANDARD", "MATHEMATICS BASIC", "APPLIED MATHEMATICS",
        "SOCIAL SCIENCE", "SANSKRIT", "HISTORY", "GEOGRAPHY", "POLITICAL SCIENCE", "ECONOMICS",
        "BUSINESS STUDIES", "ACCOUNTANCY"
    ]

    # Check for misaligned Painting (70-mark practical) and Computer Science (30-mark practical) rows in Class 12
    painting_subj = next((s for s in marksheet.subjects if "PAINTING" in s.name.upper() or "FINE ART" in s.name.upper()), None)
    cs_subj = next((s for s in marksheet.subjects if "COMPUTER" in s.name.upper() or "INFORMATICS" in s.name.upper()), None)
    if painting_subj and cs_subj:
        if painting_subj.practical is not None and painting_subj.practical <= 30.0 and cs_subj.practical is not None and cs_subj.practical >= 50.0:
            painting_subj.theory, cs_subj.theory = cs_subj.theory, painting_subj.theory
            painting_subj.practical, cs_subj.practical = cs_subj.practical, painting_subj.practical
            painting_subj.total, cs_subj.total = cs_subj.total, painting_subj.total
            warnings.append("Class 12 Layout: Restored 70-mark practical to Painting and 30-mark practical to Computer Science")

    # 2. Arithmetic reconciliation
    for subj in marksheet.subjects:
        norm_subj = subj.name.strip().upper()

        # Sanitize inflated subject max_marks (e.g. 500/600 grand total copied into subject)
        if subj.max_marks is not None and subj.max_marks > 200.0:
            subj.max_marks = 100.0

        # Sanitize inflated subject total (e.g. 425/450 grand total copied into subject row)
        if subj.total is not None and subj.total > 200.0:
            if subj.theory is not None and subj.theory <= 100.0:
                if subj.practical is not None and subj.practical <= 75.0 and subj.practical != subj.theory:
                    subj.total = subj.theory + subj.practical
                else:
                    subj.total = subj.theory
                    subj.practical = None
                subj.max_marks = 100.0
                warnings.append(f"{subj.name}: Corrected inflated total to score {subj.total}")

        # 2-Column shift detection (Single-Score / State Boards: Max marks in Theory, Min pass in Practical)
        min_pass_thresholds = [30.0, 33.0, 35.0, 36.0, 40.0, 44.0, 45.0]
        max_marks_standards = [75.0, 100.0, 125.0, 150.0, 200.0]
        if subj.theory in max_marks_standards and subj.practical in min_pass_thresholds:
            grade_num = parse_numeric_grade(subj.grade)
            subj.max_marks = subj.theory
            subj.theory = None
            subj.practical = None
            if subj.total is not None and subj.total <= subj.max_marks and subj.total not in max_marks_standards:
                warnings.append(
                    f"{subj.name}: Stripped Max/Min pass marks from Theory/Practical (Total={subj.total}, Max={subj.max_marks})"
                )
            elif grade_num is not None:
                subj.total = grade_num
                subj.grade = None
                warnings.append(
                    f"{subj.name}: Corrected column-shift (Max={subj.max_marks} -> Total={subj.total})"
                )
            continue

        # Single-Score Board: If Total was filled with 100 (Max Marks) and Theory has the actual score
        if (is_haryana or is_karnataka) and subj.total in [100.0, 125.0] and subj.theory is not None and subj.theory < subj.total:
            subj.max_marks = subj.total
            subj.total = subj.theory
            subj.theory = None
            subj.practical = None
            warnings.append(f"{subj.name}: Single-score board: Set Total to scored marks {subj.total} (Max={subj.max_marks})")
            continue

        # If practical was duplicated from total (e.g. Theory 62, Practical 82, Total 82)
        if subj.practical is not None and subj.total is not None and subj.practical == subj.total:
            if subj.theory is not None and subj.theory < subj.total:
                diff = round(subj.total - subj.theory, 2)
                if 0 < diff <= 75:
                    subj.practical = diff
                    warnings.append(
                        f"{subj.name}: Reconciled duplicated practical from Total to {diff} "
                        f"(Total {subj.total} - Theory {subj.theory})"
                    )
            else:
                subj.practical = None

        # Duplicated Practical from Theory (e.g. Theory=79, Practical=79 for non-practical subject)
        # Note: Do not reset if theory + practical == total (e.g. IT 50 + 50 = 100)
        if subj.practical is not None and subj.theory is not None and subj.practical == subj.theory:
            if subj.total is None or subj.total == subj.theory or subj.total > 100.0 or (subj.theory + subj.practical != subj.total):
                subj.practical = None
                subj.total = subj.theory
                subj.max_marks = 100.0
                warnings.append(f"{subj.name}: Practical reset to null because Theory equals Practical ({subj.theory})")

        # Swapped Theory and Practical in standard academic subjects (e.g. Theory=20, Practical=62 -> swap)
        if norm_subj in STANDARD_THEORY_SUBJS:
            if subj.theory is not None and subj.practical is not None and subj.practical > 30.0 and subj.theory <= 30.0:
                old_th, old_pr = subj.theory, subj.practical
                subj.theory, subj.practical = old_pr, old_th
                warnings.append(
                    f"{subj.name}: Corrected swapped Theory ({old_th} -> {subj.theory}) and Practical ({old_pr} -> {subj.practical})"
                )

        # If ICSE: practical is always null
        if is_icse:
            subj.practical = None
            if subj.total is not None:
                subj.theory = subj.total
            continue

        # If total is missing:
        if subj.total is None:
            if subj.theory is not None and subj.practical is not None:
                subj.total = subj.theory + subj.practical
                warnings.append(f"{subj.name}: Auto-calculated Total to {subj.total} ({subj.theory} + {subj.practical})")
            elif subj.theory is not None and subj.practical is None:
                subj.total = subj.theory
                warnings.append(f"{subj.name}: Auto-set Total to Theory ({subj.theory})")
        # Conversely, if theory is missing but total is present and practical is None:
        elif subj.theory is None and subj.total is not None and subj.practical is None:
            pass  # Single-score marksheet (e.g. State board / Karnataka SSLC)

        # If total is present and theory is present, but practical is missing:
        if not is_haryana and not is_karnataka and subj.total is not None and subj.theory is not None and subj.practical is None:
            diff = round(subj.total - subj.theory, 2)
            if 0 < diff <= 75:
                subj.practical = diff
                warnings.append(
                    f"{subj.name}: Auto-reconciled practical/internal assessment to {diff} "
                    f"(Total {subj.total} - Theory {subj.theory})"
                )

        # Self-healing: if theory equals total, practical was blank/zero
        if subj.theory is not None and subj.total is not None and subj.theory == subj.total and subj.practical is not None:
            subj.practical = None
            warnings.append(f"{subj.name}: Practical reset to null because Theory equals Total ({subj.total})")

        # Self-healing: subject total cannot exceed max marks
        max_limit = subj.max_marks or 100.0
        if subj.total is not None and subj.total > max_limit:
            if subj.theory is not None and subj.theory <= max_limit and subj.practical is not None and subj.theory + subj.practical == subj.total:
                subj.max_marks = max(max_limit, subj.total)
            elif subj.theory is not None and subj.theory <= max_limit:
                subj.total = subj.theory
                subj.practical = None
                warnings.append(f"{subj.name}: Total exceeded {max_limit}; reset to Theory {subj.theory}")

        # Self-healing: Theory + Practical cannot exceed max marks
        if subj.theory is not None and subj.practical is not None:
            if (subj.theory + subj.practical) > max_limit:
                old_prac = subj.practical
                subj.practical = None
                if subj.total is None or subj.total > max_limit:
                    subj.total = subj.theory
                warnings.append(
                    f"{subj.name}: Practical reset to null because Theory ({subj.theory}) + "
                    f"Practical ({old_prac}) exceeds max marks {max_limit}"
                )

        if subj.theory is None or subj.practical is None or subj.total is None:
            continue

        expected = subj.theory + subj.practical

        if abs(expected - subj.total) > 1:
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
    board_text = ((marksheet.board or "") + " " + (marksheet.examination or "")).upper()
    is_karnataka = "KARNATAKA" in board_text

    academic_subjs = [
        s for s in marksheet.subjects
        if s.total is not None and s.total > 0
        and "INTERNAL ASSESSMENT" not in s.name.upper()
        and "SUPW" not in s.name.upper()
    ]

    if not academic_subjs:
        return warnings

    sum_obtained = sum(s.total for s in academic_subjs)
    if is_karnataka:
        sum_max = 625.0
    else:
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
    if marksheet.result.maximum_marks is None or marksheet.result.maximum_marks > sum_max or marksheet.result.maximum_marks < (marksheet.result.total_obtained or 0):
        marksheet.result.maximum_marks = sum_max

    # 3. Percentage reconciliation — only compute if not already provided or clearly broken
    has_valid_pct = bool(
        marksheet.result.percentage and
        any(c.isdigit() for c in marksheet.result.percentage) and
        "%" in marksheet.result.percentage
    )
    if not has_valid_pct:
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

    # Step 1: Reconcile board identity if institutional location conflicts
    board_warnings = reconcile_board_identity(marksheet)

    # Step 2: Reconcile ICSE component sub-papers into aggregate subjects
    icse_warnings = reconcile_icse_subjects(marksheet)

    # Step 3: Run arithmetic sanity checks
    arith_warnings = check_arithmetic(marksheet)

    # Step 4: Reconcile grand total & percentage if missing or partial
    agg_warnings = reconcile_aggregate_results(marksheet)

    warnings = board_warnings + icse_warnings + arith_warnings + agg_warnings
    return marksheet, warnings
