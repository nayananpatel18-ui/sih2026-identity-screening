"""Focused M6 tests using synthetic TD3 MRZ values only."""

from app.data.models import EvidenceState
from app.services.mrz_adapter import MrzAdapter, mrz_check_digit


def _valid_td3() -> str:
    line_one = "P<UTODOE<<JANE<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    document_number = "D12345678"
    dob = "900101"
    expiry = "300101"
    optional_data = "<<<<<<<<<<<<<<"
    line_two_without_composite = (
        f"{document_number}{mrz_check_digit(document_number)}UTO{dob}{mrz_check_digit(dob)}F"
        f"{expiry}{mrz_check_digit(expiry)}{optional_data}{mrz_check_digit(optional_data)}"
    )
    composite = mrz_check_digit(
        line_two_without_composite[0:10]
        + line_two_without_composite[13:20]
        + line_two_without_composite[21:43]
    )
    return f"{line_one}\n{line_two_without_composite}{composite}"


def test_valid_td3_parses_and_validates():
    result = MrzAdapter().validate(_valid_td3())
    assert result.evidence_state == EvidenceState.POSITIVE
    assert all(result.check_digits.values())
    assert result.parsed_fields["document_number"] == "D12345678"
    assert result.parsed_fields["surname"] == "DOE"
    assert result.parsed_fields["given_names"] == "JANE"


def test_invalid_checksum_identifies_failed_field():
    lines = _valid_td3().splitlines()
    lines[1] = f"{lines[1][:9]}0{lines[1][10:]}"
    result = MrzAdapter().validate("\n".join(lines))
    assert result.evidence_state == EvidenceState.NEGATIVE
    assert "document_number_check_digit_failed" in result.errors


def test_missing_and_incomplete_mrz_are_not_negative():
    missing = MrzAdapter().validate(None)
    incomplete = MrzAdapter().validate("P<UTO<<<\nD123")
    unreadable = MrzAdapter().validate("P<UTO???????????????????????????????????????\nUNREADABLE")
    assert missing.evidence_state == EvidenceState.MISSING
    assert incomplete.evidence_state == EvidenceState.UNRELIABLE
    assert unreadable.evidence_state == EvidenceState.UNRELIABLE


if __name__ == "__main__":
    test_valid_td3_parses_and_validates()
    test_invalid_checksum_identifies_failed_field()
    test_missing_and_incomplete_mrz_are_not_negative()
    print("[SUCCESS] MRZ adapter tests passed.")
