"""Focused M11 tests for deterministic, evidence-grounded officer review."""

from app.data.models import (
    ConflictItem,
    ConflictType,
    EvidenceSignal,
    EvidenceState,
    RiskLevel,
    SignalCategory,
    SignalSeverity,
)
from app.services.officer_review import OfficerReviewService


def _signal(state: EvidenceState, *, source: str = "OCR", contribution: float = 0.0, title: str | None = None) -> EvidenceSignal:
    return EvidenceSignal(
        signal_id=f"SIG_{source}_{state.value}", source=source,
        category=SignalCategory.DOCUMENT_INTELLIGENCE, evidence_state=state,
        severity=SignalSeverity.HIGH if state == EvidenceState.NEGATIVE else SignalSeverity.INFO,
        title=title or f"{state.value} evidence", description="Synthetic test evidence.",
        confidence=0.9, contribution=contribution,
        limitation="Synthetic test limitation." if state in (EvidenceState.MISSING, EvidenceState.UNAVAILABLE, EvidenceState.UNRELIABLE) else None,
    )


def _conflict() -> ConflictItem:
    return ConflictItem(
        conflict_id="CONF_CROSS_DOB", source_a="PASSPORT", source_b="VISA", field_name="dob",
        value_a="2007-11-11", value_b="1997-11-11", conflict_type=ConflictType.ACTUAL_CONTRADICTION,
        severity=SignalSeverity.HIGH, confidence=0.9, impact=0.1, explanation="Normalized DOB values differ.",
    )


def _review(level: RiskLevel, signals=None, conflicts=None, uncertainty: float = 0.0):
    return OfficerReviewService().build(
        screening_id="SCR-TEST", risk_level=level, risk_score=0.0 if level in (RiskLevel.GREEN, RiskLevel.GREY) else 0.4,
        uncertainty_score=uncertainty, signals=signals or [], conflicts=conflicts or [], recommendation="Officer recommendation.",
    )


def test_green_review_has_supporting_findings_and_human_decision_requirement():
    review = _review(RiskLevel.GREEN, [_signal(EvidenceState.POSITIVE, source="MRZ")])
    assert "broadly consistent" in review.overall_assessment
    assert review.key_positive_findings[0].source == "MRZ"
    assert not review.key_suspicious_findings
    assert review.human_decision_required is True


def test_amber_review_surfaces_suspicious_evidence_and_recommendations():
    review = _review(RiskLevel.AMBER, [_signal(EvidenceState.NEGATIVE, source="MRZ", contribution=0.4)])
    assert review.key_suspicious_findings
    assert any("MRZ" in recommendation for recommendation in review.recommended_verifications)


def test_red_review_prioritizes_conflicts_and_manual_inspection_language():
    review = _review(RiskLevel.RED, [_signal(EvidenceState.NEGATIVE, contribution=0.4)], [_conflict()])
    assert review.conflicts[0].field_name == "dob"
    assert "strongly recommended" in review.overall_assessment
    assert any("date of birth" in recommendation.lower() for recommendation in review.recommended_verifications)


def test_grey_review_explains_unreliable_evidence():
    review = _review(RiskLevel.GREY, [_signal(EvidenceState.UNRELIABLE, source="VISUAL_FORENSICS")], uncertainty=0.8)
    assert review.uncertainty_reasons
    assert any("quality limitations" in recommendation for recommendation in review.recommended_verifications)


def test_missing_evidence_is_not_described_as_fraud():
    review = _review(RiskLevel.GREY, [_signal(EvidenceState.MISSING)], uncertainty=0.7)
    assert review.key_suspicious_findings == []
    assert any("missing" in reason.lower() for reason in review.uncertainty_reasons)


def test_unavailable_evidence_is_not_described_as_negative():
    review = _review(RiskLevel.GREY, [_signal(EvidenceState.UNAVAILABLE)], uncertainty=0.7)
    assert review.key_suspicious_findings == []
    assert any("unavailable" in reason.lower() for reason in review.uncertainty_reasons)


def test_unreliable_evidence_is_not_described_as_contradiction():
    review = _review(RiskLevel.GREY, [_signal(EvidenceState.UNRELIABLE)], uncertainty=0.7)
    assert review.conflicts == []
    assert review.key_suspicious_findings == []


def test_cross_document_conflict_preserves_context_and_traceability():
    review = _review(RiskLevel.AMBER, [_signal(EvidenceState.NEGATIVE, source="CROSS_DOCUMENT", contribution=0.1)], [_conflict()])
    conflict = review.conflicts[0]
    assert conflict.source_a == "PASSPORT"
    assert conflict.value_b == "1997-11-11"
    assert review.key_suspicious_findings[0].signal_id == "SIG_CROSS_DOCUMENT_NEGATIVE"


def test_officer_review_contains_no_ground_truth():
    review = _review(RiskLevel.GREEN, [_signal(EvidenceState.POSITIVE)])
    assert "ground_truth" not in str(review.model_dump()).lower()


def test_officer_review_is_deterministic_for_same_input():
    signals = [_signal(EvidenceState.POSITIVE, source="MRZ"), _signal(EvidenceState.UNRELIABLE, source="OCR")]
    first = _review(RiskLevel.AMBER, signals, [_conflict()], uncertainty=0.2)
    second = _review(RiskLevel.AMBER, signals, [_conflict()], uncertainty=0.2)
    assert first.model_dump() == second.model_dump()


if __name__ == "__main__":
    test_green_review_has_supporting_findings_and_human_decision_requirement()
    test_amber_review_surfaces_suspicious_evidence_and_recommendations()
    test_red_review_prioritizes_conflicts_and_manual_inspection_language()
    test_grey_review_explains_unreliable_evidence()
    test_missing_evidence_is_not_described_as_fraud()
    test_unavailable_evidence_is_not_described_as_negative()
    test_unreliable_evidence_is_not_described_as_contradiction()
    test_cross_document_conflict_preserves_context_and_traceability()
    test_officer_review_contains_no_ground_truth()
    test_officer_review_is_deterministic_for_same_input()
    print("[SUCCESS] Officer review tests passed.")
