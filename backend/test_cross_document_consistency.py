"""Focused M9 tests for deterministic structured cross-document comparisons."""

from app.data.models import CanonicalExtractedFields, EvidenceState
from app.services.cross_document_consistency import (
    ComparableDocument,
    CrossDocumentConsistencyEngine,
)
from app.services.risk_engine import compute_risk_score


def _document(document_id: str, document_type: str, **fields) -> ComparableDocument:
    return ComparableDocument(document_id, document_type, CanonicalExtractedFields(**fields))


def test_consistent_fields_and_equivalent_formats_do_not_create_conflicts():
    passport = _document("PASSPORT", "PASSPORT", full_name="NAYANA PATEL", dob="11-11-2007", nationality="IND")
    visa = _document("VISA", "VISA", full_name="PATEL, NAYANA", dob="2007/11/11", nationality="ind")
    signals, conflicts = CrossDocumentConsistencyEngine().analyze([passport, visa])

    assert not conflicts
    assert any(signal.evidence_state == EvidenceState.POSITIVE and signal.raw_details["field"] == "dob" for signal in signals)
    assert compute_risk_score(signals, conflicts) == 0.0


def test_reliable_dob_contradiction_creates_conflict_and_negative_evidence():
    passport = _document("PASSPORT", "PASSPORT", full_name="NAYANA PATEL", dob="2007-11-11")
    national_id = _document("NATIONAL_ID", "NATIONAL_ID", full_name="NAYANA PATEL", dob="1997-11-11")
    signals, conflicts = CrossDocumentConsistencyEngine().analyze([passport, national_id])

    dob_signal = next(signal for signal in signals if signal.raw_details["field"] == "dob")
    assert dob_signal.source == "CROSS_DOCUMENT"
    assert dob_signal.evidence_state == EvidenceState.NEGATIVE
    assert dob_signal.contribution > 0.0
    assert len(conflicts) == 1
    assert conflicts[0].field_name == "dob"
    assert conflicts[0].value_a == "2007-11-11"
    assert compute_risk_score(signals, conflicts) > 0.0


def test_missing_and_unreliable_fields_do_not_create_contradictions_or_risk():
    passport = _document("PASSPORT", "PASSPORT", full_name="NAYANA PATEL", dob="2007-11-11")
    missing_visa = _document("VISA", "VISA", full_name="NAYANA PATEL")
    missing_signals, missing_conflicts = CrossDocumentConsistencyEngine().analyze([passport, missing_visa])
    assert any(signal.raw_details["field"] == "dob" and signal.evidence_state == EvidenceState.MISSING for signal in missing_signals)
    assert not missing_conflicts
    assert compute_risk_score(missing_signals, missing_conflicts) == 0.0

    unreliable_visa = ComparableDocument(
        "VISA", "VISA", CanonicalExtractedFields(full_name="NAYANA PATEL", dob="2007-11-XX"),
        field_states={"dob": EvidenceState.UNRELIABLE},
    )
    unreliable_signals, unreliable_conflicts = CrossDocumentConsistencyEngine().analyze([passport, unreliable_visa])
    assert any(signal.raw_details["field"] == "dob" and signal.evidence_state == EvidenceState.UNRELIABLE for signal in unreliable_signals)
    assert not unreliable_conflicts
    assert compute_risk_score(unreliable_signals, unreliable_conflicts) == 0.0


def test_different_identifier_types_are_not_compared_and_multiple_documents_are_paired():
    passport = _document("PASSPORT", "PASSPORT", full_name="NAYANA PATEL", dob="2007-11-11", document_number="P123")
    national_id = _document("NATIONAL_ID", "NATIONAL_ID", full_name="NAYANA PATEL", dob="2007-11-11", document_number="ID999")
    visa = _document("VISA", "VISA", full_name="NAYANA PATEL", dob="2007-11-11", document_number="V777")
    signals, conflicts = CrossDocumentConsistencyEngine().analyze([passport, national_id, visa])

    number_signals = [signal for signal in signals if signal.raw_details["field"] == "document_number"]
    assert len(number_signals) == 3
    assert all(signal.evidence_state == EvidenceState.NOT_APPLICABLE for signal in number_signals)
    assert not conflicts


if __name__ == "__main__":
    test_consistent_fields_and_equivalent_formats_do_not_create_conflicts()
    test_reliable_dob_contradiction_creates_conflict_and_negative_evidence()
    test_missing_and_unreliable_fields_do_not_create_contradictions_or_risk()
    test_different_identifier_types_are_not_compared_and_multiple_documents_are_paired()
    print("[SUCCESS] Cross-document consistency tests passed.")
