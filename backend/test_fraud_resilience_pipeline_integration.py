"""M12 service/API-facing integration checks without normal screening changes."""

import app.data.synthetic_adapter

from app.services.fraud_resilience import FraudResilienceService


def test_all_controlled_scenarios_evaluate_to_expected_responses():
    summary = FraudResilienceService().evaluate_all()
    assert summary["scenario_count"] == 9
    assert summary["expected_response_count"] == 9
    assert summary["unexpected_response_count"] == 0


def test_public_scenario_catalog_omits_internal_expectations():
    scenarios = FraudResilienceService().list_scenarios()
    assert len(scenarios) == 9
    assert "expected_categories" not in str(scenarios)
    assert "ground_truth" not in str(scenarios).lower()


if __name__ == "__main__":
    test_all_controlled_scenarios_evaluate_to_expected_responses()
    test_public_scenario_catalog_omits_internal_expectations()
    print("[SUCCESS] Fraud resilience integration tests passed.")
