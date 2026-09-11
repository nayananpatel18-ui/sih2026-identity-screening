"""
Verification script for Milestone 1: Canonical Models & SyntheticDataAdapter.
"""

from app.data.synthetic_adapter import SyntheticDataAdapter
from app.data.base import DatasetRegistry


def test_synthetic_adapter():
    print("--- Testing Milestone 1 Data Adapter ---")
    adapter = DatasetRegistry.get("synthetic")
    assert adapter is not None, "SyntheticDataAdapter not registered in DatasetRegistry!"
    
    samples = adapter.list_samples()
    print(f"Available samples in dataset '{adapter.dataset_name}': {samples}")
    assert len(samples) >= 3, f"Expected at least 3 demo samples, found {len(samples)}"
    
    for sample_id in samples:
        sample = adapter.get_sample(sample_id)
        assert sample is not None, f"Sample '{sample_id}' returned None!"
        print(f"\n[Sample]: {sample.sample_id}")
        print(f"  - Document Type: {sample.document_type}")
        print(f"  - Ground Truth Risk: {sample.ground_truth.expected_risk if sample.ground_truth else 'N/A'}")
        print(f"  - Full Name: {sample.extracted_fields.full_name if sample.extracted_fields else 'N/A'}")
        print(f"  - Sufficient Quality: {sample.quality_metadata.is_sufficient_quality}")

    print("\n[SUCCESS] Canonical models and SyntheticDataAdapter verified successfully!")


if __name__ == "__main__":
    test_synthetic_adapter()
