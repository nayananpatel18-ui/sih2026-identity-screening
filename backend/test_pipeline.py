"""
End-to-end pipeline verification for Milestones 3 & 4.
Validates that all three synthetic demo cases produce expected risk outcomes.
"""

from app.data.base import DatasetRegistry
from app.data.models import RiskLevel
from app.services.pipeline import run_screening_pipeline
import app.data.synthetic_adapter  # registers adapter

EXPECTED = {
    "CASE_001_GENUINE": RiskLevel.GREEN,
    "CASE_002_TAMPERED": RiskLevel.RED,
    "CASE_003_UNCERTAIN": RiskLevel.GREY,
}


def test_pipeline():
    print("=== Milestone 4 — Deterministic Pipeline Verification ===\n")
    adapter = DatasetRegistry.get("synthetic")
    assert adapter, "SyntheticDataAdapter not found in registry!"

    passed = 0
    for sample_id, expected_risk in EXPECTED.items():
        sample = adapter.get_sample(sample_id)
        assert sample, f"Sample '{sample_id}' not found!"

        result = run_screening_pipeline(sample)

        status = "PASS" if result.risk_level == expected_risk else "FAIL"
        print(f"[{status}] {sample_id}")
        print(f"  Risk Level    : {result.risk_level} (expected {expected_risk})")
        print(f"  Risk Score    : {result.risk_score:.4f}")
        print(f"  Uncertainty   : {result.uncertainty_score:.4f}")
        print(f"  Biometric     : {result.biometric_result}")
        print(f"  Signals       : {len(result.evidence_signals)}")
        print(f"  Conflicts     : {len(result.conflicts)}")
        print(f"  Explanation   : {result.explanation[:120]}...")
        print(f"  Recommendation: {result.recommendation[:80]}...")
        print()

        if status == "PASS":
            passed += 1
        else:
            print(f"  !!! EXPECTED {expected_risk}, GOT {result.risk_level} !!!")

    print(f"Result: {passed}/{len(EXPECTED)} cases passed.")
    assert passed == len(EXPECTED), "One or more demo cases produced unexpected risk outcomes!"
    print("\n[SUCCESS] All three demo cases verified successfully.")


if __name__ == "__main__":
    test_pipeline()
