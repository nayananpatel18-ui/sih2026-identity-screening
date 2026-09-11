"""
Synthetic Data Adapter Implementation.
Loads synthetic identity screening cases from the datasets/synthetic directory.
"""

import os
import json
from typing import List, Optional, Dict
from app.data.base import BaseDataAdapter, DatasetRegistry
from app.data.models import (
    CanonicalDocumentSample,
    CanonicalExtractedFields,
    QualityMetadata,
    GroundTruthMetadata,
    TamperMetadata,
    DocumentType,
    RiskLevel
)


class SyntheticDataAdapter(BaseDataAdapter):
    """
    Adapter for loading controlled synthetic demo datasets.
    Provides standard CanonicalDocumentSample instances to the screening pipeline.
    """

    def __init__(self, manifest_path: str = "datasets/synthetic/manifest.json"):
        self.manifest_path = manifest_path
        self._samples_cache: Dict[str, CanonicalDocumentSample] = {}
        self.reload()

    @property
    def dataset_name(self) -> str:
        return "synthetic"

    def reload(self):
        """Load samples from manifest JSON file if present."""
        self._samples_cache.clear()
        if not os.path.exists(self.manifest_path):
            # Fallback path if running from backend root directory
            alt_path = os.path.join("..", self.manifest_path)
            if os.path.exists(alt_path):
                self.manifest_path = alt_path

        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("samples", []):
                        sample = self._parse_sample_dict(item)
                        self._samples_cache[sample.sample_id] = sample
            except Exception as e:
                print(f"[SyntheticDataAdapter] Error loading manifest: {e}")

    def _parse_sample_dict(self, item: dict) -> CanonicalDocumentSample:
        ext_fields_data = item.get("extracted_fields")
        ext_fields = CanonicalExtractedFields(**ext_fields_data) if ext_fields_data else None

        qual_data = item.get("quality_metadata", {})
        qual_metadata = QualityMetadata(**qual_data)

        gt_data = item.get("ground_truth")
        gt_metadata = None
        if gt_data:
            tamper_d = gt_data.get("tamper_details")
            t_meta = TamperMetadata(**tamper_d) if tamper_d else None
            gt_metadata = GroundTruthMetadata(
                is_tampered=gt_data.get("is_tampered", False),
                expected_risk=RiskLevel(gt_data.get("expected_risk", "GREEN")),
                tamper_details=t_meta
            )

        return CanonicalDocumentSample(
            sample_id=item["sample_id"],
            source_dataset="synthetic",
            document_type=DocumentType(item.get("document_type", "PASSPORT")),
            document_image=item.get("document_image", ""),
            secondary_document_image=item.get("secondary_document_image"),
            person_image=item.get("person_image"),
            extracted_fields=ext_fields,
            quality_metadata=qual_metadata,
            ground_truth=gt_metadata
        )

    def list_samples(self) -> List[str]:
        return list(self._samples_cache.keys())

    def get_sample(self, sample_id: str) -> Optional[CanonicalDocumentSample]:
        return self._samples_cache.get(sample_id)

    def get_sample_by_case_type(self, case_type: str) -> Optional[CanonicalDocumentSample]:
        target_map = {
            "genuine": "CASE_001_GENUINE",
            "tampered": "CASE_002_TAMPERED",
            "uncertain": "CASE_003_UNCERTAIN"
        }
        sample_id = target_map.get(case_type.lower(), case_type)
        return self.get_sample(sample_id)


# Auto-register synthetic adapter on import
default_synthetic_adapter = SyntheticDataAdapter()
DatasetRegistry.register(default_synthetic_adapter)
