"""
validate.py — Validate and clean marksheet data from the VLM.

Uses Pydantic for type-safe schemas and adds arithmetic sanity checks
(theory + practical should equal total marks).

This catches VLM mistakes before the data reaches the user.
"""

from typing import Optional
from pydantic import BaseModel, field_validator


# ── Schema Models ─────────────────────────────────────────────────────────────
# These define the exact shape of a valid marksheet extraction.

class Subject(BaseModel):
    """One subject row from the marksheet."""
    name: str = ""
    theory: Optional[float] = None
    practical: Optional[float] = None
    total: Optional[float] = None
    max_marks: Optional[float] = None
    grade: Optional[str] = None


class StudentInfo(BaseModel):
    """Student details from the top section of the marksheet."""
    name: Optional[str] = None
    roll_no: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    school_name: Optional[str] = None
    dob: Optional[str] = None


class Result(BaseModel):
    """Overall result summary from the bottom of the marksheet."""
    total_obtained: Optional[float] = None
    maximum_marks: Optional[float] = None
    percentage: Optional[str] = None
    status: Optional[str] = None

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

    Returns a list of warning strings (empty = all good).
    Allows ±1 tolerance for rounding differences.
    """
    warnings = []

    for subj in marksheet.subjects:
        # Only check when all three values are present
        if subj.theory is None or subj.practical is None or subj.total is None:
            continue

        expected = subj.theory + subj.practical

        if abs(expected - subj.total) > 1:
            # Self-healing: if model recorded maximum marks (e.g. 100) as total obtained,
            # reconcile total = theory + practical and preserve maximum marks.
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

    return marksheet, warnings
