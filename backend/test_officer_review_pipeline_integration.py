"""Focused M11 opt-in pipeline integration tests."""

import app.data.synthetic_adapter
from app.data.base import DatasetRegistry
from app.data.models import RiskLevel
from app.services.pipeline import run_screening_pipeline


def _sample(sample_id: str):
    sample = DatasetRegistry.get("synthetic").get_sample(sample_id)
    assert sample
    return sample


def test_officer_review_is_disabled_by_default():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"))
    assert result.officer_review is None


def test_opt_in_review_uses_existing_evidence_without_fusion_requirement():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"), enable_officer_review=True)
    assert result.risk_level == RiskLevel.GREEN
    assert result.officer_review
    assert result.officer_review.human_decision_required is True
    assert "ground_truth" not in str(result.officer_review.model_dump()).lower()


def test_opt_in_review_preserves_cases_and_surfaces_m9_conflict():
    expected = {
        "CASE_001_GENUINE": RiskLevel.GREEN,
        "CASE_002_TAMPERED": RiskLevel.RED,
        "CASE_003_UNCERTAIN": RiskLevel.GREY,
    }
    for sample_id, level in expected.items():
        result = run_screening_pipeline(
            _sample(sample_id),
            enable_cross_document_consistency=True,
            enable_evidence_fusion=True,
            enable_officer_review=True,
        )
        assert result.risk_level == level
        assert result.officer_review and result.officer_review.risk_level == level
        if sample_id == "CASE_002_TAMPERED":
            assert any(conflict.field_name == "dob" for conflict in result.officer_review.conflicts)


if __name__ == "__main__":
    test_officer_review_is_disabled_by_default()
    test_opt_in_review_uses_existing_evidence_without_fusion_requirement()
    test_opt_in_review_preserves_cases_and_surfaces_m9_conflict()
    print("[SUCCESS] Officer review pipeline integration tests passed.")
