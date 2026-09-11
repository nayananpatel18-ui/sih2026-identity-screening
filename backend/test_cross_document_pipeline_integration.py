"""Focused M9 opt-in pipeline checks."""

import app.data.synthetic_adapter
from app.data.base import DatasetRegistry
from app.data.models import EvidenceState, RiskLevel
from app.services.pipeline import run_screening_pipeline


def _sample(sample_id: str):
    sample = DatasetRegistry.get("synthetic").get_sample(sample_id)
    assert sample
    return sample


def test_cross_document_is_disabled_by_default():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"))
    assert not any(signal.source == "CROSS_DOCUMENT" for signal in result.evidence_signals)


def test_opt_in_adds_consistency_evidence_without_risk_increase():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"), enable_cross_document_consistency=True)
    signals = [signal for signal in result.evidence_signals if signal.source == "CROSS_DOCUMENT"]
    assert result.risk_level == RiskLevel.GREEN
    assert signals
    assert any(signal.evidence_state == EvidenceState.POSITIVE for signal in signals)
    assert result.risk_score == 0.0


def test_opt_in_detects_structured_dob_conflict_and_preserves_regressions():
    result = run_screening_pipeline(_sample("CASE_002_TAMPERED"), enable_cross_document_consistency=True)
    conflict = next(conflict for conflict in result.conflicts if conflict.conflict_id == "CONF_CROSS_PRIMARY_VISA_002_DOB")
    assert conflict.field_name == "dob"
    assert result.risk_level == RiskLevel.RED

    uncertain = run_screening_pipeline(_sample("CASE_003_UNCERTAIN"), enable_cross_document_consistency=True)
    signal = next(signal for signal in uncertain.evidence_signals if signal.source == "CROSS_DOCUMENT")
    assert signal.evidence_state == EvidenceState.MISSING
    assert uncertain.risk_level == RiskLevel.GREY


if __name__ == "__main__":
    test_cross_document_is_disabled_by_default()
    test_opt_in_adds_consistency_evidence_without_risk_increase()
    test_opt_in_detects_structured_dob_conflict_and_preserves_regressions()
    print("[SUCCESS] Cross-document pipeline integration tests passed.")
