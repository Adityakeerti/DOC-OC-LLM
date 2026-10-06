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
        s = re.sub(r"^(Mr\.|Mrs\.|Smt\.|Shri|Master|Km\.|Miss)\s+", "", s, flags=re.IGNORECASE).strip()
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
        "INTERNAL ASSESSMENT", "SUPW", "OVERALL RESULT", "RESULT"
    ]
    cleaned_subjects = []
    for s in marksheet.subjects:
        norm_name = s.name.strip().upper()
        if any(norm_name == b or norm_name.startswith(b + " ") for b in BOGUS_LABELS) and len(norm_name) <= 22:
            warnings.append(f"Filtered out non-academic category label row: '{s.name}'")
            continue
        cleaned_subjects.append(s)
    marksheet.subjects = cleaned_subjects

    # 2. Arithmetic reconciliation
    for subj in marksheet.subjects:
        # If total is present and theory is present, but practical is missing:
        if subj.total is not None and subj.theory is not None:
            diff = round(subj.total - subj.theory, 2)
            if subj.practical is None and 0 < diff <= 50:
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

        # 2d. Self-healing: Theory + Practical cannot exceed max marks (e.g. 89 + 20 = 109 > 100)
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
            else:
                warnings.append(
                    f"{subj.name}: {subj.theory} + {subj.practical} = {expected}, "
                    f"but total shows {subj.total}"
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
    if curr_total is None or (curr_total < sum_obtained * 0.4 and len(academic_subjs) >= 3):
        marksheet.result.total_obtained = sum_obtained
        warnings.append(
            f"Auto-reconciled grand total obtained to {sum_obtained} from {len(academic_subjs)} academic subjects"
        )

    # 2. Maximum marks reconciliation
    if marksheet.result.maximum_marks is None or marksheet.result.maximum_marks < marksheet.result.total_obtained:
        marksheet.result.maximum_marks = sum_max

    # 3. Percentage reconciliation
    if not marksheet.result.percentage and marksheet.result.maximum_marks:
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

    # Run arithmetic sanity checks
    warnings = check_arithmetic(marksheet)

    # Reconcile grand total & percentage if missing or partial
    agg_warnings = reconcile_aggregate_results(marksheet)
    warnings.extend(agg_warnings)

    return marksheet, warnings
