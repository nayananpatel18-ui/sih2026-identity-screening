"""Focused M10 tests for bounded, explainable multimodal evidence fusion."""

from app.data.models import (
    ConflictItem,
    ConflictType,
    EvidenceSignal,
    EvidenceState,
    QualityMetadata,
    SignalCategory,
    SignalSeverity,
)
from app.services.evidence_fusion import MultimodalEvidenceFusionEngine, fusion_evidence_signal


def _signal(state: EvidenceState, contribution: float = 0.0, confidence: float = 1.0, source: str = "TEST") -> EvidenceSignal:
    return EvidenceSignal(
        signal_id=f"SIG_{source}_{state.value}", source=source,
        category=SignalCategory.DOCUMENT_INTELLIGENCE, evidence_state=state,
        severity=SignalSeverity.INFO, title=f"{state.value} evidence", description="Synthetic test evidence.",
        confidence=confidence, contribution=contribution,
    )


def _conflict(confidence: float = 1.0, impact: float = 0.10) -> ConflictItem:
    return ConflictItem(
        conflict_id="CONF_TEST", source_a="PASSPORT", source_b="VISA", field_name="dob",
        value_a="2007-11-11", value_b="1997-11-11", conflict_type=ConflictType.ACTUAL_CONTRADICTION,
        severity=SignalSeverity.HIGH, confidence=confidence, impact=impact,
        explanation="Synthetic reliable DOB contradiction.",
    )


def _fuse(signals, conflicts=None):
    return MultimodalEvidenceFusionEngine().fuse(signals, conflicts or [], QualityMetadata())


def test_reliable_positive_evidence_is_low_risk_and_low_uncertainty():
    result = _fuse([_signal(EvidenceState.POSITIVE, source="OCR"), _signal(EvidenceState.POSITIVE, source="MRZ")])
    assert result.risk_score == 0.0
    assert result.uncertainty_score == 0.0
    assert result.risk_level.value == "GREEN"
    assert result.coverage["positive_count"] == 2


def test_one_reliable_negative_signal_increases_bounded_risk():
    result = _fuse([_signal(EvidenceState.NEGATIVE, contribution=0.20)])
    assert result.risk_score == 0.20
    assert result.risk_level.value == "GREEN"


def test_multiple_reliable_negative_signals_can_reach_red():
    result = _fuse([_signal(EvidenceState.NEGATIVE, 0.40, source="MRZ"), _signal(EvidenceState.NEGATIVE, 0.40, source="VISUAL")])
    assert result.risk_score == 0.80
    assert result.risk_level.value == "RED"


def test_missing_evidence_does_not_raise_risk():
    result = _fuse([_signal(EvidenceState.MISSING)])
    assert result.risk_score == 0.0
    assert result.uncertainty_score == 0.15
    assert result.coverage["missing_count"] == 1


def test_unavailable_evidence_does_not_raise_risk():
    result = _fuse([_signal(EvidenceState.UNAVAILABLE)])
    assert result.risk_score == 0.0
    assert result.uncertainty_score == 0.30


def test_unreliable_evidence_increases_uncertainty_not_risk():
    result = _fuse([_signal(EvidenceState.UNRELIABLE)])
    assert result.risk_score == 0.0
    assert result.uncertainty_score == 0.30


def test_actual_cross_document_conflict_is_preserved_and_bounded():
    result = _fuse([_signal(EvidenceState.POSITIVE)], [_conflict()])
    assert result.risk_score == 0.10
    assert result.important_conflicts[0]["field_name"] == "dob"


def test_conflict_and_unreliable_evidence_keep_risk_and_uncertainty_distinct():
    result = _fuse([_signal(EvidenceState.UNRELIABLE), _signal(EvidenceState.POSITIVE, source="MRZ")], [_conflict()])
    assert result.risk_score == 0.10
    assert result.uncertainty_score == 0.15
    assert result.risk_score != result.uncertainty_score


def test_empty_evidence_set_is_safe_and_routes_to_grey():
    result = _fuse([])
    assert result.risk_score == 0.0
    assert result.uncertainty_score == 0.70
    assert result.risk_level.value == "GREY"


def test_fused_officer_facing_details_do_not_include_ground_truth():
    result = _fuse([_signal(EvidenceState.POSITIVE)])
    signal = fusion_evidence_signal(result)
    assert signal.source == "EVIDENCE_FUSION"
    assert signal.contribution == 0.0
    assert "ground_truth" not in str(signal.raw_details).lower()


if __name__ == "__main__":
    test_reliable_positive_evidence_is_low_risk_and_low_uncertainty()
    test_one_reliable_negative_signal_increases_bounded_risk()
    test_multiple_reliable_negative_signals_can_reach_red()
    test_missing_evidence_does_not_raise_risk()
    test_unavailable_evidence_does_not_raise_risk()
    test_unreliable_evidence_increases_uncertainty_not_risk()
    test_actual_cross_document_conflict_is_preserved_and_bounded()
    test_conflict_and_unreliable_evidence_keep_risk_and_uncertainty_distinct()
    test_empty_evidence_set_is_safe_and_routes_to_grey()
    test_fused_officer_facing_details_do_not_include_ground_truth()
    print("[SUCCESS] Evidence fusion tests passed.")
