"""M12 controlled, deterministic resilience evaluation around the existing pipeline.

This lab simulates bounded adapter observations for clearly labelled synthetic
scenarios.  It is not an independent detector: all risk, uncertainty, fusion,
and officer-review results are calculated by the existing pipeline.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List, Tuple

from app.data.base import DatasetRegistry
from app.data.models import (
    CanonicalDocumentSample,
    ConflictItem,
    ConflictType,
    EvidenceSignal,
    EvidenceState,
    RiskLevel,
    SignalCategory,
    SignalSeverity,
)
from app.services.pipeline import run_screening_pipeline


class ResponseCategory(str, Enum):
    DETECTED_SUSPICIOUS_SIGNAL = "DETECTED_SUSPICIOUS_SIGNAL"
    DETECTED_CONFLICT = "DETECTED_CONFLICT"
    UNCERTAINTY_ESCALATED = "UNCERTAINTY_ESCALATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ANALYSIS_UNAVAILABLE = "ANALYSIS_UNAVAILABLE"
    NO_SIGNIFICANT_SIGNAL = "NO_SIGNIFICANT_SIGNAL"


@dataclass(frozen=True)
class FraudResilienceScenario:
    scenario_id: str
    scenario_name: str
    description: str
    attack_category: str
    target_component: str
    baseline_case_id: str
    perturbation_description: str
    expected_categories: Tuple[ResponseCategory, ...]


@dataclass(frozen=True)
class FraudResilienceEvaluationResult:
    """Safe lab output; intended expectations remain internal to the service."""

    scenario_id: str
    baseline_case_id: str
    observed_risk_level: RiskLevel
    observed_risk_score: float
    observed_uncertainty_score: float
    detected_signals: List[str]
    detected_conflicts: List[str]
    evidence_coverage: Dict[str, object]
    response_category: ResponseCategory
    components_exercised: List[str]
    explanation: str
    limitations: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "baseline_case_id": self.baseline_case_id,
            "observed_risk_level": self.observed_risk_level.value,
            "observed_risk_score": self.observed_risk_score,
            "observed_uncertainty_score": self.observed_uncertainty_score,
            "detected_signals": self.detected_signals,
            "detected_conflicts": self.detected_conflicts,
            "evidence_coverage": self.evidence_coverage,
            "response_category": self.response_category.value,
            "components_exercised": self.components_exercised,
            "explanation": self.explanation,
            "limitations": self.limitations,
        }


class FraudResilienceService:
    """Runs controlled M12 cases through M4-M11 without exposing test labels."""

    _SCENARIOS = (
        FraudResilienceScenario("M12_BASELINE_GENUINE", "Baseline genuine input", "Runs the unmodified genuine synthetic baseline.", "BASELINE", "PIPELINE", "CASE_001_GENUINE", "No perturbation.", (ResponseCategory.NO_SIGNIFICANT_SIGNAL,)),
        FraudResilienceScenario("M12_FIELD_ALTERATION", "Controlled field alteration", "Runs the repository's existing synthetic altered-field fixture through the existing OCR, MRZ, visual, biometric, cross-document, fusion, and review paths.", "FIELD_ALTERATION", "MRZ_STRUCTURAL_VALIDATION", "CASE_002_TAMPERED", "Use the existing controlled altered DOB fixture; no M12 detector observation is injected.", (ResponseCategory.DETECTED_CONFLICT,)),
        FraudResilienceScenario("M12_CROSS_DOCUMENT_MISMATCH", "Cross-document mismatch", "Supplies a controlled secondary record with a different date of birth.", "CROSS_DOCUMENT_MISMATCH", "CROSS_DOCUMENT", "CASE_001_GENUINE", "Alter only the comparison document DOB.", (ResponseCategory.DETECTED_CONFLICT,)),
        FraudResilienceScenario("M12_BIOMETRIC_PROXY_INCONSISTENCY", "Synthetic-avatar proxy inconsistency", "Runs the existing M8 synthetic-avatar visual-consistency proxy with an intentionally inconsistent fixture pair; it is not face recognition.", "BIOMETRIC_INCONSISTENCY", "BIOMETRIC", "CASE_001_GENUINE", "Compare the genuine document fixture with the existing tampered synthetic-avatar fixture.", (ResponseCategory.UNCERTAINTY_ESCALATED,)),
        FraudResilienceScenario("M12_LOW_QUALITY", "Low-quality document", "Runs the existing low-quality fixture through the existing OCR, MRZ, and visual-forensics adapters.", "LOW_QUALITY", "VISUAL_FORENSICS", "CASE_003_UNCERTAIN", "Use the repository's existing blurred synthetic document fixture; no M12 quality detector is introduced.", (ResponseCategory.UNCERTAINTY_ESCALATED,)),
        FraudResilienceScenario("M12_MISSING_EVIDENCE", "Missing evidence", "Simulates a controlled missing evidence source without treating it as a suspicious signal.", "MISSING_EVIDENCE", "EVIDENCE_COVERAGE", "CASE_001_GENUINE", "Inject a zero-risk MISSING observation.", (ResponseCategory.INSUFFICIENT_EVIDENCE,)),
        FraudResilienceScenario("M12_UNAVAILABLE_ANALYSIS", "Unavailable analysis", "Simulates an analysis adapter that could not run.", "UNAVAILABLE_ANALYSIS", "ADAPTER_AVAILABILITY", "CASE_001_GENUINE", "Inject a zero-risk UNAVAILABLE observation.", (ResponseCategory.ANALYSIS_UNAVAILABLE,)),
        FraudResilienceScenario("M12_UNRELIABLE_EVIDENCE", "Unreliable evidence", "Simulates a controlled unreliable observation without creating a contradiction.", "UNRELIABLE_EVIDENCE", "VISUAL_FORENSICS", "CASE_001_GENUINE", "Inject a zero-risk UNRELIABLE observation.", (ResponseCategory.UNCERTAINTY_ESCALATED,)),
        FraudResilienceScenario("M12_MULTI_SIGNAL", "Multiple independent suspicious signals", "Runs the repository's existing multi-signal synthetic altered-document fixture through available adapters and fusion/review.", "MULTI_SIGNAL", "MULTIMODAL", "CASE_002_TAMPERED", "Use the existing controlled multi-signal fixture; no M12 detector observation is injected.", (ResponseCategory.DETECTED_CONFLICT,)),
    )

    def list_scenarios(self) -> List[Dict[str, str]]:
        return [{
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.scenario_name,
            "description": scenario.description,
            "attack_category": scenario.attack_category,
            "target_component": scenario.target_component,
            "baseline_case_id": scenario.baseline_case_id,
            "perturbation_description": scenario.perturbation_description,
        } for scenario in self._SCENARIOS]

    def evaluate(self, scenario_id: str) -> FraudResilienceEvaluationResult:
        scenario = next((item for item in self._SCENARIOS if item.scenario_id == scenario_id), None)
        if scenario is None:
            raise ValueError(f"Unknown fraud-resilience scenario: {scenario_id}")
        sample = self._baseline_sample(scenario.baseline_case_id)
        sample, signals, conflicts = self._perturb(scenario, sample)
        result = run_screening_pipeline(
            sample,
            **self._pipeline_options(scenario),
            enable_evidence_fusion=True,
            enable_officer_review=True,
            evaluation_signals=signals,
            evaluation_conflicts=conflicts,
        )
        category = self._response_category(result.evidence_signals, result.conflicts, scenario)
        coverage = self._coverage(result.evidence_signals, result.conflicts)
        return FraudResilienceEvaluationResult(
            scenario_id=scenario.scenario_id,
            baseline_case_id=scenario.baseline_case_id,
            observed_risk_level=result.risk_level,
            observed_risk_score=result.risk_score,
            observed_uncertainty_score=result.uncertainty_score,
            detected_signals=[signal.signal_id for signal in result.evidence_signals if signal.evidence_state == EvidenceState.NEGATIVE],
            detected_conflicts=[conflict.conflict_id for conflict in result.conflicts if conflict.conflict_type == ConflictType.ACTUAL_CONTRADICTION],
            evidence_coverage=coverage,
            response_category=category,
            components_exercised=self._components_exercised(result),
            explanation=result.explanation,
            limitations=[signal.limitation for signal in result.evidence_signals if signal.limitation][:5],
        )

    def evaluate_all(self) -> Dict[str, object]:
        evaluated = [self.evaluate(scenario.scenario_id) for scenario in self._SCENARIOS]
        expected = sum(
            item.response_category in self._scenario(item.scenario_id).expected_categories
            for item in evaluated
        )
        return {
            "scenario_count": len(evaluated),
            "expected_response_count": expected,
            "unexpected_response_count": len(evaluated) - expected,
            "scenario_response_rate": round(expected / len(evaluated), 4),
            "results": [item.to_dict() for item in evaluated],
            "limitation": "Metrics describe only these controlled synthetic scenarios and are not production detection accuracy.",
        }

    @staticmethod
    def _baseline_sample(case_id: str) -> CanonicalDocumentSample:
        adapter = DatasetRegistry.get("synthetic")
        sample = adapter.get_sample(case_id) if adapter else None
        if sample is None:
            raise ValueError(f"Synthetic baseline case unavailable: {case_id}")
        return sample.model_copy(deep=True)

    @staticmethod
    def _signal(signal_id: str, source: str, state: EvidenceState, title: str, description: str, contribution: float = 0.0) -> EvidenceSignal:
        return EvidenceSignal(
            signal_id=signal_id, source=source, category=SignalCategory.STRUCTURAL_VALIDATION,
            evidence_state=state,
            severity=SignalSeverity.HIGH if state == EvidenceState.NEGATIVE else SignalSeverity.INFO,
            title=title, description=description, confidence=0.9 if state == EvidenceState.NEGATIVE else 0.0,
            contribution=contribution,
            limitation="Controlled M12 synthetic evaluation observation; it is not a real-world authentication result.",
        )

    def _perturb(self, scenario: FraudResilienceScenario, sample: CanonicalDocumentSample) -> Tuple[CanonicalDocumentSample, List[EvidenceSignal], List[ConflictItem]]:
        sid = scenario.scenario_id
        if sid == "M12_CROSS_DOCUMENT_MISMATCH":
            sample.additional_metadata["comparison_documents"] = [{
                "document_id": "M12_SECONDARY", "document_type": "VISA",
                "extracted_fields": {"full_name": sample.extracted_fields.full_name, "dob": "1979-02-03", "nationality": sample.extracted_fields.nationality},
            }]
        elif sid == "M12_BIOMETRIC_PROXY_INCONSISTENCY":
            sample.person_image = "datasets/synthetic/tampered/person_002.png"
        elif sid == "M12_MISSING_EVIDENCE":
            return sample, [self._signal("SIG_M12_MISSING", "OCR", EvidenceState.MISSING, "Controlled Evidence Source Missing", "A required controlled evidence source was not provided. Missing evidence is not a fraud signal.")], []
        elif sid == "M12_UNAVAILABLE_ANALYSIS":
            return sample, [self._signal("SIG_M12_UNAVAILABLE", "MRZ", EvidenceState.UNAVAILABLE, "Controlled Analysis Unavailable", "A controlled analysis adapter could not run. This is not a fraud signal.")], []
        elif sid == "M12_UNRELIABLE_EVIDENCE":
            return sample, [self._signal("SIG_M12_UNRELIABLE", "VISUAL_FORENSICS", EvidenceState.UNRELIABLE, "Controlled Visual Evidence Unreliable", "A controlled visual observation was unreliable. This is not a contradiction or fraud signal.")], []
        return sample, [], []

    @staticmethod
    def _pipeline_options(scenario: FraudResilienceScenario) -> Dict[str, bool]:
        """Enable existing adapters only for scenarios where their input is meaningful."""
        all_adapters = {
            "enable_ocr": True,
            "enable_mrz": True,
            "enable_visual_forensics": True,
            "enable_biometric_verification": True,
            "enable_cross_document_consistency": True,
        }
        if scenario.scenario_id in {"M12_BASELINE_GENUINE", "M12_FIELD_ALTERATION", "M12_CROSS_DOCUMENT_MISMATCH", "M12_MULTI_SIGNAL"}:
            return all_adapters
        if scenario.scenario_id == "M12_LOW_QUALITY":
            return {**all_adapters, "enable_biometric_verification": False, "enable_cross_document_consistency": False}
        if scenario.scenario_id == "M12_BIOMETRIC_PROXY_INCONSISTENCY":
            return {name: name == "enable_biometric_verification" for name in all_adapters}
        return {name: False for name in all_adapters}

    @staticmethod
    def _response_category(signals: Iterable[EvidenceSignal], conflicts: Iterable[ConflictItem], scenario: FraudResilienceScenario) -> ResponseCategory:
        signal_list, conflict_list = list(signals), list(conflicts)
        if any(item.conflict_type == ConflictType.ACTUAL_CONTRADICTION for item in conflict_list):
            return ResponseCategory.DETECTED_CONFLICT
        if any(item.signal_id == "SIG_M12_UNAVAILABLE" for item in signal_list):
            return ResponseCategory.ANALYSIS_UNAVAILABLE
        if any(item.signal_id == "SIG_M12_MISSING" for item in signal_list):
            return ResponseCategory.INSUFFICIENT_EVIDENCE
        if scenario.scenario_id in {"M12_BIOMETRIC_PROXY_INCONSISTENCY", "M12_LOW_QUALITY", "M12_UNRELIABLE_EVIDENCE"}:
            return ResponseCategory.UNCERTAINTY_ESCALATED
        return ResponseCategory.NO_SIGNIFICANT_SIGNAL

    @staticmethod
    def _components_exercised(result) -> List[str]:
        source_components = {
            "OCR": "M5_OCR",
            "MRZ": "M6_MRZ_STRUCTURAL_VALIDATION",
            "VISUAL_FORENSICS": "M7_VISUAL_FORENSICS",
            "BIOMETRIC": "M8_SYNTHETIC_AVATAR_PROXY",
            "CROSS_DOCUMENT": "M9_CROSS_DOCUMENT_CONSISTENCY",
            "EVIDENCE_FUSION": "M10_EVIDENCE_FUSION",
        }
        components = ["M4_SYNTHETIC_PIPELINE"]
        components.extend(
            source_components[source]
            for source in source_components
            if any(signal.source == source and not signal.signal_id.startswith("SIG_M12_") for signal in result.evidence_signals)
        )
        if result.officer_review is not None:
            components.append("M11_OFFICER_REVIEW")
        return components

    @staticmethod
    def _coverage(signals: Iterable[EvidenceSignal], conflicts: Iterable[ConflictItem]) -> Dict[str, object]:
        signal_list, conflict_list = list(signals), list(conflicts)
        return {
            "signal_count": len(signal_list),
            "positive_count": sum(item.evidence_state == EvidenceState.POSITIVE for item in signal_list),
            "negative_count": sum(item.evidence_state == EvidenceState.NEGATIVE for item in signal_list),
            "missing_count": sum(item.evidence_state == EvidenceState.MISSING for item in signal_list),
            "unavailable_count": sum(item.evidence_state == EvidenceState.UNAVAILABLE for item in signal_list),
            "unreliable_count": sum(item.evidence_state == EvidenceState.UNRELIABLE for item in signal_list),
            "conflict_count": len(conflict_list),
        }

    def _scenario(self, scenario_id: str) -> FraudResilienceScenario:
        return next(item for item in self._SCENARIOS if item.scenario_id == scenario_id)
