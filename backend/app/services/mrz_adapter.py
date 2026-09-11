"""Isolated TD3 MRZ parser and structural validator for M6.

This validates MRZ layout and check digits only.  It does not authenticate a
document, verify identity, or establish fraud.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from app.data.models import (
    CanonicalDocumentSample,
    EvidenceSignal,
    EvidenceState,
    SignalCategory,
    SignalSeverity,
)


_WEIGHTS = (7, 3, 1)
_CHAR_VALUES = {str(number): number for number in range(10)}
_CHAR_VALUES.update({chr(ord("A") + index): 10 + index for index in range(26)})
_CHAR_VALUES["<"] = 0


@dataclass
class MrzValidationResult:
    normalized_mrz: str = ""
    parsed_fields: Dict[str, str] = field(default_factory=dict)
    check_digits: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    evidence_state: EvidenceState = EvidenceState.MISSING
    limitation: str = "MRZ validation checks structural consistency only; it does not prove authenticity."


class MrzAdapter:
    """Parser for TD3 passport MRZs containing two 44-character lines."""

    def validate(self, mrz_text: str | None) -> MrzValidationResult:
        if mrz_text is None or not mrz_text.strip():
            return MrzValidationResult(
                evidence_state=EvidenceState.MISSING,
                errors=["mrz_missing"],
            )

        lines = [line.strip().upper().replace(" ", "") for line in mrz_text.replace("\r\n", "\n").split("\n") if line.strip()]
        normalized = "\n".join(lines)
        if any("?" in line or "UNREADABLE" in line for line in lines):
            return MrzValidationResult(
                normalized_mrz=normalized,
                errors=["mrz_unreliable_characters"],
                evidence_state=EvidenceState.UNRELIABLE,
            )
        if len(lines) != 2 or any(len(line) != 44 for line in lines):
            return MrzValidationResult(
                normalized_mrz=normalized,
                errors=["td3_requires_two_44_character_lines"],
                evidence_state=EvidenceState.UNRELIABLE,
            )
        if any(character not in _CHAR_VALUES for line in lines for character in line):
            return MrzValidationResult(
                normalized_mrz=normalized,
                errors=["mrz_contains_invalid_characters"],
                evidence_state=EvidenceState.NEGATIVE,
            )

        line_one, line_two = lines
        parsed_fields = _parse_td3_fields(line_one, line_two)
        check_digits = {
            "document_number": _matches_check_digit(line_two[0:9], line_two[9]),
            "date_of_birth": _matches_check_digit(line_two[13:19], line_two[19]),
            "date_of_expiry": _matches_check_digit(line_two[21:27], line_two[27]),
            "optional_data": _matches_check_digit(line_two[28:42], line_two[42]),
            "composite": _matches_check_digit(line_two[0:10] + line_two[13:20] + line_two[21:43], line_two[43]),
        }
        failures = [f"{name}_check_digit_failed" for name, valid in check_digits.items() if not valid]
        return MrzValidationResult(
            normalized_mrz=normalized,
            parsed_fields=parsed_fields,
            check_digits=check_digits,
            errors=failures,
            evidence_state=EvidenceState.NEGATIVE if failures else EvidenceState.POSITIVE,
        )


def mrz_check_digit(value: str) -> str:
    """Calculate the ICAO 9303 weighted check digit for valid MRZ characters."""
    return str(sum(_CHAR_VALUES[character] * _WEIGHTS[index % 3] for index, character in enumerate(value)) % 10)


def _matches_check_digit(value: str, supplied_digit: str) -> bool:
    return supplied_digit.isdigit() and mrz_check_digit(value) == supplied_digit


def _parse_td3_fields(line_one: str, line_two: str) -> Dict[str, str]:
    name_parts = line_one[5:44].rstrip("<").split("<<", 1)
    surname = name_parts[0].replace("<", " ").strip()
    given_names = name_parts[1].replace("<", " ").strip() if len(name_parts) == 2 else ""
    return {
        "document_type": line_one[0:2].rstrip("<"),
        "issuing_state": line_one[2:5],
        "surname": surname,
        "given_names": given_names,
        "document_number": line_two[0:9].replace("<", ""),
        "nationality": line_two[10:13],
        "date_of_birth": line_two[13:19],
        "sex": line_two[20],
        "date_of_expiry": line_two[21:27],
        "optional_data": line_two[28:42].rstrip("<"),
    }


def extract_mrz_evidence(sample: CanonicalDocumentSample, adapter: MrzAdapter | None = None) -> List[EvidenceSignal]:
    """Map TD3 validation to explicit structural evidence without altering risk thresholds."""
    mrz_text = sample.extracted_fields.mrz_raw if sample.extracted_fields else None
    result = (adapter or MrzAdapter()).validate(mrz_text)
    raw_details = {
        "normalized_mrz": result.normalized_mrz,
        "parsed_fields": result.parsed_fields,
        "check_digits": result.check_digits,
        "validation_errors": result.errors,
        "format": "TD3",
    }

    if result.evidence_state == EvidenceState.POSITIVE:
        title = "MRZ Structure and Check Digits Valid"
        description = "TD3 MRZ structure and applicable check digits are internally consistent. This does not authenticate the document."
        confidence, severity = 1.0, SignalSeverity.INFO
    elif result.evidence_state == EvidenceState.NEGATIVE:
        title = "MRZ Structural Validation Failed"
        description = f"MRZ validation failed: {', '.join(result.errors)}. This is a structural discrepancy requiring review, not proof of fraud."
        confidence, severity = 1.0, SignalSeverity.HIGH
    elif result.evidence_state == EvidenceState.MISSING:
        title = "MRZ Not Available"
        description = "No MRZ was supplied for structural validation. Missing MRZ is not a fraud signal."
        confidence, severity = 0.0, SignalSeverity.INFO
    else:
        title = "MRZ Unreliable or Incomplete"
        description = "MRZ text is incomplete, damaged, or unreadable, so structural validation could not be performed. This is not a fraud signal."
        confidence, severity = 0.25, SignalSeverity.HIGH

    return [EvidenceSignal(
        signal_id=f"SIG_MRZ_RUNTIME_{sample.sample_id}",
        source="MRZ",
        category=SignalCategory.STRUCTURAL_VALIDATION,
        evidence_state=result.evidence_state,
        severity=severity,
        title=title,
        description=description,
        confidence=confidence,
        # M6 exposes structural evidence only; risk weighting stays unchanged.
        contribution=0.0,
        limitation=result.limitation,
        raw_details=raw_details,
    )]
