"""Deterministic M9 cross-document consistency checks over structured fields.

This service compares only fields already supplied by the data/OCR layer.  It
does not infer missing values, resolve identities, or treat unavailable data as
a contradiction.
"""

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Dict, Iterable, List, Optional, Tuple

from app.data.models import (
    CanonicalDocumentSample,
    CanonicalExtractedFields,
    ConflictItem,
    ConflictType,
    EvidenceSignal,
    EvidenceState,
    SignalCategory,
    SignalSeverity,
)


COMPARABLE_FIELDS = ("full_name", "dob", "nationality", "gender", "document_number")
IDENTITY_CRITICAL_FIELDS = {"dob", "document_number"}


@dataclass(frozen=True)
class ComparableDocument:
    document_id: str
    document_type: str
    fields: CanonicalExtractedFields
    field_states: Dict[str, EvidenceState] = field(default_factory=dict)
    field_confidence: Dict[str, float] = field(default_factory=dict)
    identifier_group: Optional[str] = None


def normalize_name(value: str) -> Optional[str]:
    tokens = re.findall(r"[A-Z0-9]+", value.upper())
    if not tokens:
        return None
    # Sorting tokens safely handles "PATEL, NAYANA" / "NAYANA PATEL" only.
    return " ".join(sorted(tokens))


def normalize_dob(value: str) -> Optional[str]:
    value = value.strip()
    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    return None


def normalize_field(field_name: str, value: str) -> Optional[str]:
    if field_name == "full_name":
        return normalize_name(value)
    if field_name == "dob":
        return normalize_dob(value)
    if field_name in {"nationality", "gender", "document_number"}:
        normalized = re.sub(r"[\s\-]", "", value.upper())
        return normalized or None
    return None


def documents_from_sample(sample: CanonicalDocumentSample) -> List[ComparableDocument]:
    """Build M9 inputs from existing primary fields and optional structured metadata."""
    documents = [ComparableDocument(
        document_id="PRIMARY",
        document_type=sample.document_type.value,
        fields=sample.extracted_fields or CanonicalExtractedFields(),
    )]
    for index, raw_document in enumerate(sample.additional_metadata.get("comparison_documents", []), start=1):
        fields_data = raw_document.get("extracted_fields", {})
        state_data = raw_document.get("field_states", {})
        documents.append(ComparableDocument(
            document_id=raw_document.get("document_id", f"SECONDARY_{index}"),
            document_type=raw_document.get("document_type", "UNKNOWN"),
            fields=CanonicalExtractedFields(**fields_data),
            field_states={key: EvidenceState(value) for key, value in state_data.items()},
            field_confidence=raw_document.get("field_confidence", {}),
            identifier_group=raw_document.get("identifier_group"),
        ))
    return documents


class CrossDocumentConsistencyEngine:
    """Pairwise, explainable comparisons that preserve missing-data semantics."""

    def analyze(self, documents: Iterable[ComparableDocument]) -> Tuple[List[EvidenceSignal], List[ConflictItem]]:
        document_list = list(documents)
        if len(document_list) < 2:
            return [self._evidence(
                "availability", EvidenceState.MISSING, SignalSeverity.INFO, 0.0, 0.0,
                "Cross-Document Comparison Not Available",
                "Fewer than two structured documents were available for comparison. Missing evidence is not a fraud signal.",
                {"document_count": len(document_list)},
            )], []

        signals: List[EvidenceSignal] = []
        conflicts: List[ConflictItem] = []
        for left_index, left in enumerate(document_list):
            for right in document_list[left_index + 1:]:
                pair_signals, pair_conflicts = self._compare_pair(left, right)
                signals.extend(pair_signals)
                conflicts.extend(pair_conflicts)
        return signals, conflicts

    def _compare_pair(self, left: ComparableDocument, right: ComparableDocument) -> Tuple[List[EvidenceSignal], List[ConflictItem]]:
        signals: List[EvidenceSignal] = []
        conflicts: List[ConflictItem] = []
        for field_name in COMPARABLE_FIELDS:
            if field_name == "document_number" and not self._numbers_are_comparable(left, right):
                signals.append(self._evidence(
                    field_name, EvidenceState.NOT_APPLICABLE, SignalSeverity.INFO, 0.0, 0.0,
                    "Document Numbers Not Compared",
                    "Document numbers were not compared because no shared identifier relationship was supplied.",
                    self._details(left, right, field_name),
                ))
                continue

            left_value = getattr(left.fields, field_name)
            right_value = getattr(right.fields, field_name)
            left_state = left.field_states.get(field_name)
            right_state = right.field_states.get(field_name)
            details = self._details(left, right, field_name, left_value, right_value)
            if left_state == EvidenceState.UNRELIABLE or right_state == EvidenceState.UNRELIABLE:
                signals.append(self._evidence(
                    field_name, EvidenceState.UNRELIABLE, SignalSeverity.INFO, 0.0, 0.0,
                    f"{field_name} Comparison Unreliable",
                    f"{field_name} could not be compared reliably across {left.document_type} and {right.document_type}. This is not a contradiction.",
                    details,
                ))
                continue
            if left_state == EvidenceState.UNAVAILABLE or right_state == EvidenceState.UNAVAILABLE:
                signals.append(self._evidence(
                    field_name, EvidenceState.UNAVAILABLE, SignalSeverity.INFO, 0.0, 0.0,
                    f"{field_name} Comparison Unavailable",
                    f"{field_name} was unavailable from at least one document. This is not a contradiction.",
                    details,
                ))
                continue
            if not left_value or not right_value:
                signals.append(self._evidence(
                    field_name, EvidenceState.MISSING, SignalSeverity.INFO, 0.0, 0.0,
                    f"{field_name} Comparison Missing",
                    f"{field_name} was missing from at least one document, so no cross-document conclusion was made.",
                    details,
                ))
                continue

            left_normalized = normalize_field(field_name, left_value)
            right_normalized = normalize_field(field_name, right_value)
            details["normalized_value_a"] = left_normalized
            details["normalized_value_b"] = right_normalized
            if not left_normalized or not right_normalized:
                signals.append(self._evidence(
                    field_name, EvidenceState.UNRELIABLE, SignalSeverity.INFO, 0.0, 0.0,
                    f"{field_name} Normalization Unreliable",
                    f"{field_name} could not be normalized confidently, so no contradiction was created.",
                    details,
                ))
                continue

            confidence = min(left.field_confidence.get(field_name, 1.0), right.field_confidence.get(field_name, 1.0))
            if left_normalized == right_normalized:
                signals.append(self._evidence(
                    field_name, EvidenceState.POSITIVE, SignalSeverity.INFO, confidence, 0.0,
                    f"Cross-Document {field_name} Consistent",
                    f"{field_name} was consistent across {left.document_type} and {right.document_type} after normalization.",
                    details,
                ))
                continue

            severity = SignalSeverity.HIGH if field_name in IDENTITY_CRITICAL_FIELDS else SignalSeverity.MEDIUM
            contribution = 0.10 if field_name in IDENTITY_CRITICAL_FIELDS else 0.05
            signals.append(self._evidence(
                field_name, EvidenceState.NEGATIVE, severity, confidence, contribution,
                f"Cross-Document {field_name} Inconsistency",
                f"{field_name} differs between sufficiently available {left.document_type} and {right.document_type} records. This requires officer review and is not proof of fraud.",
                details,
            ))
            conflicts.append(ConflictItem(
                conflict_id=f"CONF_CROSS_{left.document_id}_{right.document_id}_{field_name}".upper(),
                source_a=left.document_id,
                source_b=right.document_id,
                field_name=field_name,
                value_a=left_value,
                value_b=right_value,
                conflict_type=ConflictType.ACTUAL_CONTRADICTION,
                severity=severity,
                confidence=confidence,
                impact=contribution,
                resolvable=True,
                resolution_status="UNRESOLVED",
                explanation=f"Normalized {field_name} values differ across {left.document_type} and {right.document_type}; secondary inspection may be appropriate.",
            ))
        return signals, conflicts

    @staticmethod
    def _numbers_are_comparable(left: ComparableDocument, right: ComparableDocument) -> bool:
        return bool(left.identifier_group and left.identifier_group == right.identifier_group)

    @staticmethod
    def _details(left: ComparableDocument, right: ComparableDocument, field_name: str, value_a: Optional[str] = None, value_b: Optional[str] = None) -> Dict[str, object]:
        return {
            "document_a": {"id": left.document_id, "type": left.document_type},
            "document_b": {"id": right.document_id, "type": right.document_type},
            "field": field_name,
            "value_a": value_a,
            "value_b": value_b,
        }

    @staticmethod
    def _evidence(field_name: str, state: EvidenceState, severity: SignalSeverity, confidence: float, contribution: float, title: str, description: str, details: Dict[str, object]) -> EvidenceSignal:
        return EvidenceSignal(
            signal_id=f"SIG_CROSS_RUNTIME_{details['document_a']['id']}_{details['document_b']['id']}_{field_name}".upper() if "document_a" in details else "SIG_CROSS_RUNTIME_AVAILABILITY",
            source="CROSS_DOCUMENT",
            category=SignalCategory.CROSS_DOCUMENT_CONSISTENCY,
            evidence_state=state,
            severity=severity,
            title=title,
            description=description,
            confidence=confidence,
            contribution=contribution,
            limitation="Cross-document consistency identifies available field agreement or disagreement only; it does not verify identity or document authenticity.",
            raw_details=details,
        )


def extract_cross_document_evidence(sample: CanonicalDocumentSample) -> Tuple[List[EvidenceSignal], List[ConflictItem]]:
    """Pipeline adapter for M9; data is limited to existing structured sample fields."""
    return CrossDocumentConsistencyEngine().analyze(documents_from_sample(sample))
