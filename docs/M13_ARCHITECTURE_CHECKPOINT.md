# M13 Architecture & Integration Checkpoint

## 1. Executive Summary

This checkpoint was prepared from the repository at commit `8b39c8f` on `main`.
The backend has a coherent deterministic evidence pipeline: M4 supplies baseline
synthetic evidence, optional adapters enrich it, M9 creates explicit conflicts,
M10 reuses the established risk/uncertainty functions, and M11 creates advisory
officer-review output. M12 is a separate, opt-in resilience harness that invokes
the same pipeline rather than owning a second risk/fusion/review engine.

The main integration gaps are at the product boundary, not in the core pipeline:

- uploads are validated and written to local temporary storage but cannot create
  a screening;
- the React client calls the default screening API only, so it neither enables
  M5-M11 options nor renders `officer_review`;
- the Fraud Lab page is a static frontend demo and does not call the M12 API;
- Firebase Admin/Firestore fallback code already exists, but Firebase Auth and
  Storage do not, and persistence is not yet a complete authenticated data model.

Two real privacy concerns should be resolved before treating synthetic demo
responses as an officer-facing production contract: normal sample/screening
responses expose synthetic case IDs such as `CASE_002_TAMPERED`, and inherited
M4 limitations include the phrase "ground-truth metadata." The model field
`ground_truth` itself is excluded from `/api/samples/{sample_id}` and does not
appear in `MultimodalScreeningResult`, but those strings still reveal evaluation
context.

## 2. Verified M1-M12 Architecture

`backend/app/main.py` registers health, samples, upload, screenings, and M12
fraud-resilience routes under `/api`. `backend/app/services/pipeline.py` is the
single screening orchestrator.

1. `SyntheticDataAdapter` loads `datasets/synthetic/manifest.json` into
   `CanonicalDocumentSample` objects.
2. `run_screening_pipeline` calls M4 `extract_synthetic_evidence` first.
3. Opt-in M5-M9 adapters append `EvidenceSignal` objects and, for M9, explicit
   `ConflictItem` objects.
4. M10 optionally calls `MultimodalEvidenceFusionEngine.fuse`; otherwise the
   same M4 risk functions are called directly.
5. `generate_explanation` and `get_recommendation` create decision-support
   wording. M11 optionally calls `OfficerReviewService.build`.
6. The `/api/screenings/run` route persists `result.model_dump()` through the
   existing `FirestoreRepository` abstraction and returns the same result.

## 3. End-to-End Data Flow

### Current upload path

`frontend/src/pages/NewScreeningPage.tsx` -> `api.uploadFile` ->
`POST /api/upload` (`backend/app/api/routes/upload.py`) -> content/extension
validation with Pillow -> `backend/temp_uploads/<uuid>.<extension>` -> upload
session metadata returned to the browser.

This path is intentionally separate from screening. The returned `file_id` is
not accepted by `POST /api/screenings/run`, and no canonical sample is created
from an upload.

### Current synthetic screening path

`NewScreeningPage` -> `App.handleStartScreening` -> `api.runScreening` ->
`POST /api/screenings/run` -> `DatasetRegistry.get("synthetic")` ->
`SyntheticDataAdapter.get_sample` -> `run_screening_pipeline` -> evidence /
conflicts / risk / uncertainty / explanation / optional M11 review ->
`FirestoreRepository.save_screening` -> JSON response ->
`App.activeScreeningResult` -> `EvidenceExplanationPage`.

The frontend request currently provides only `sample_id` and `dataset`, so all
backend opt-in flags remain false. The frontend renders risk, evidence,
conflicts, explanation, and recommendation from `MultimodalScreeningResult`.
It does not declare or render the M11 `officer_review` field.

## 4. Module Responsibility Map

| Module | Responsibility | Inputs | Outputs | Status |
|---|---|---|---|---|
| M1 data layer | Canonical samples and adapter registry | Synthetic manifest | `CanonicalDocumentSample` | Active |
| M2 UI | React/Vite navigation and pages | API responses/demo constants | Dashboard views | Active |
| M3 upload | Demo-safe image intake | `UploadFile` | Local temporary upload metadata | Active, separate from screening |
| M4 extractor | Fixed synthetic baseline evidence | `sample_id` | signals, conflicts, biometric state | Active |
| M5 OCR | Local Tesseract boundary or fixture fallback | document image | zero-risk OCR evidence | Opt-in |
| M6 MRZ | TD3 structural/check-digit validation | `mrz_raw` | MRZ evidence | Opt-in |
| M7 visual | Pillow quality/compression metrics | document image | supporting visual evidence | Opt-in |
| M8 biometric | Synthetic-avatar consistency proxy | person/document images | zero-risk biometric evidence | Opt-in |
| M9 consistency | Compare structured documents | fields/metadata | signals and `ConflictItem`s | Opt-in |
| Risk engine | Risk/uncertainty and level thresholds | quality, signals, conflicts | scores and `RiskLevel` | Shared baseline |
| M10 fusion | Summarize existing multimodal evidence | signals, conflicts, quality | fusion result and zero-risk summary signal | Opt-in |
| M11 review | Advisory officer explanation | screening evidence/conflicts/scores | `OfficerReviewResult` | Opt-in |
| M12 lab | Controlled scenario evaluation | synthetic samples + limited state injections | lab-only evaluation result | Separate opt-in API |

No M4-M12 module duplicates risk calculation, fusion, or officer review. M12
uses `run_screening_pipeline`; it enables M5-M11 where appropriate and retains
controlled injection only for MISSING, UNAVAILABLE, and UNRELIABLE resilience
states.

## 5. Evidence / Conflict / Screening Data Model

The canonical Pydantic models are in `backend/app/data/models.py`:

- `EvidenceSignal`: source/category/state/severity, confidence, contribution,
  title, description, limitation, and raw details. Confidence measures
  reliability; contribution affects risk only for `NEGATIVE` signals.
- `ConflictItem`: comparison sources/values, `ConflictType`, severity,
  confidence, impact, resolution state, and explanation. Only
  `ACTUAL_CONTRADICTION` is risk-bearing.
- `MultimodalScreeningResult`: screening identity, score/state, fields, quality,
  evidence, conflicts, biometric result, explanation, recommendation, and
  optional M11 `officer_review`.
- `OfficerReviewResult`: structured findings, actual conflicts, uncertainty
  reasons, verification suggestions, limitations, recommendation, and fixed
  `human_decision_required=True`.

M12 uses frozen dataclasses (`FraudResilienceScenario` and
`FraudResilienceEvaluationResult`) in its service. These are intentionally
separate evaluation structures and do not compete with the officer-facing
screening schema. Its `components_exercised` field is lab metadata only.

The frontend mirrors the base screening structures in `frontend/src/types/index.ts`,
but that TypeScript type currently omits `officer_review`; it also has no M12
evaluation types because the M12 page is static.

## 6. Risk + Uncertainty Flow

`backend/app/services/risk_engine.py` is authoritative:

- `compute_risk_score` sums `contribution * confidence` only for `NEGATIVE`
  signals, plus actual-conflict `impact * confidence`.
- `compute_uncertainty_score` uses quality metadata plus UNRELIABLE/UNAVAILABLE
  evidence and unreliable/unreadable conflicts. Missing comparisons are not a
  risk or base uncertainty penalty.
- `determine_risk_level` applies GREY at uncertainty `>= 0.65`, RED at risk
  `>= 0.70`, AMBER at risk `>= 0.35`, otherwise GREEN.

M10 imports and invokes these functions. It adds only bounded coverage/context
adjustments and emits a zero-contribution summary signal. M11 consumes completed
scores, signals, and conflicts; it does not compute a new score or level.

## 7. Human-in-the-Loop Boundary

M11 is advisory. `OfficerReviewService` generates findings and recommended
verifications from existing data, while its output sets
`human_decision_required=True`. The repository contains no approve, reject,
deny, admit, or autonomous clearance route. Existing recommendations use
decision-support wording and preserve an officer final-decision statement.

## 8. Privacy / Ground Truth Boundary

Verified protections:

- `GET /api/samples/{sample_id}` constructs `OfficerFacingDocumentSample` while
  excluding the `ground_truth` model field.
- `MultimodalScreeningResult` has no `ground_truth` field.
- M11 copies selected evidence/conflict fields rather than sample metadata.
- M12 normal screening cannot receive evaluation signals through
  `ScreeningRequest`; the lab has its own routes.

Real concerns to address in a future safety-focused milestone:

1. The normal sample/screening APIs still return `sample_id`; the fixed labels
   `CASE_001_GENUINE`, `CASE_002_TAMPERED`, and `CASE_003_UNCERTAIN` expose
   synthetic expected-outcome context.
2. M4 synthetic evidence limitations in `synthetic_extractor.py` include wording
   such as "derived from ground-truth metadata." Because M11 includes signal
   limitations, this wording can reach officer-review output for some cases.
3. The frontend itself displays static `EXPECTED` labels for the synthetic cases
   and static Fraud Lab expected-response text. This is clearly demo UI, but is
   unsuitable for a real officer-facing deployment.

## 9. Fraud Resilience Architecture

M12 (`fraud_resilience.py`) is a deterministic evaluation layer over the shared
pipeline. It deep-copies registered samples, uses existing fixtures/adapters
where meaningful, enables M10/M11 for every evaluation, and serializes only
lab result fields.

- baseline: actual M5-M9 paths where applicable;
- field alteration and multi-signal: existing CASE_002 fixture;
- cross-document mismatch: deep-copied structured comparison record through M9;
- biometric proxy: existing M8 inconsistent synthetic-avatar pair;
- low quality: existing CASE_003 fixture through M5-M7;
- missing/unavailable/unreliable: controlled, zero-risk state injection.

It neither implements risk scoring nor exposes M12 evaluation arguments through
normal screening. The M12 API is registered at `/api/fraud-resilience/*`.

The current React `FraudLabPage` is not connected to those endpoints; it is a
static interaction/demo and therefore should not be read as live M12 results.

## 10. Frontend Integration Boundary

Entry points:

- `App.tsx`: app state, health/sample fetches, synthetic screening launch.
- `NewScreeningPage.tsx`: preset selection and separate local upload flow.
- `EvidenceExplanationPage.tsx`: base screening risk/evidence/conflict rendering.
- `ScreeningHistoryPage.tsx`: static mock history.
- `FraudLabPage.tsx`: static lab demonstration.
- `SystemStatusPage.tsx`: health and canonical sample inspector.

The evidence view iterates arbitrary `evidence_signals` and `conflicts`; it does
not assume a fixed source list. This supports future enrichment without a model
redesign. Its TypeScript model and API client must be extended deliberately
before M11 officer-review results or live M12 results are rendered.

## 11. Current Persistence Model

| Concern | Actual current behavior |
|---|---|
| Samples/fixtures | Static JSON and local synthetic images |
| Upload bytes | `backend/temp_uploads`, local process filesystem |
| Upload metadata | Returned only; no durable repository record |
| Screenings | In-memory `FirestoreRepository._in_memory_store`; optionally Firestore when credentials initialize |
| History UI | Hard-coded mock data, not repository reads |
| Authentication | None |
| Object storage | None |

`firebase_service.py` and `firebase-admin` are already present. They are a
best-effort Firestore wrapper with local fallback, not a complete Firebase
integration. The service account path comes from configuration; no Firebase
Storage or Firebase Authentication path is implemented.

## 12. Proposed Firebase Boundary

**PROPOSED — NOT IMPLEMENTED**

Keep FastAPI responsible for authenticated request authorization, canonical
normalization, adapters, the screening pipeline, risk/uncertainty calculation,
M10/M11, and M12. Do not move document processing or future AI calls into
Firebase client code.

Firebase should provide:

- Firebase Authentication in the frontend and ID-token verification at FastAPI;
- Firebase Storage for uploaded document/person images, with retention and
  access controls;
- Firestore for screening metadata, evidence summaries, officer decisions,
  audit events, and lab-run metadata where appropriate.

Conceptual flow: frontend -> Firebase Auth -> authenticated FastAPI -> pipeline
-> Firestore/Storage persistence -> officer dashboard. The existing
`FirestoreRepository` is a possible migration seam, but its schema, ownership,
error handling, and authorization rules need design before M14.

## 13. Proposed AI Boundary

**PROPOSED — NOT IMPLEMENTED**

Place a future AI service after deterministic evidence fusion and before the
final M11 presentation layer:

`structured evidence/conflicts + deterministic risk/uncertainty -> AI risk
reasoner (advisory context only) -> AI explanation layer -> officer review`.

The AI input should be a constrained, provenance-preserving projection of
`EvidenceSignal`, `ConflictItem`, scores, uncertainty reasons, and limitations.
It must not consume raw untrusted images by default, change deterministic
thresholds, infer ground truth, or issue autonomous authenticity/legal outcomes.
M11 should remain responsible for the explicit human-decision requirement.

## 14. Configuration / Secrets Boundary

`backend/app/core/config.py` uses `pydantic-settings` with `.env` support.
`.env.example` documents server, CORS, synthetic dataset, and optional Firebase
settings. `backend/.gitignore` should continue to exclude `.env`, service-account
credentials, and generated uploads. Future AI/Firebase secrets belong in
environment variables or deployment secret storage, never source code, fixtures,
or frontend bundles.

## 15. Test Coverage

Backend tests are executable scripts named `backend/test_*.py`:

- adapter/unit coverage for M1, M5, M6, M7, M8, M9, and M10;
- pipeline integration coverage for M5-M12;
- M4 three-case deterministic regression in `test_pipeline.py`;
- M11 privacy/determinism/advisory tests;
- M12 scenario, determinism, opt-in, component-traceability, and privacy tests.

Recent validated totals: M12 14 passing tests; M4-M11 63 passing tests; the
three M4 baseline cases remain GREEN/RED/GREY. The frontend has TypeScript/Vite
build support but no frontend test runner or component/API integration tests.

Most important future test categories: Firebase token verification and Firestore
rules/emulator tests; Storage upload authorization/retention tests; repository
restart/durability tests; authenticated end-to-end upload-to-screening tests;
frontend rendering of real officer review and M12 results; AI schema validation,
prompt-injection resistance, provenance, and deterministic fallback tests.

## 16. Architectural Risks / Technical Debt

1. Uploaded files are not screenable; M3 and the synthetic screening path are
   intentionally disconnected.
2. The frontend does not use M11 or live M12 endpoints, despite backend support.
3. Mock history values and static Fraud Lab expectations can drift from backend
   behavior.
4. Existing Firebase fallback is process-local when credentials are absent and
   lacks authentication, Storage, durable upload linkage, and an explicit data
   retention model.
5. Synthetic outcome labels and the inherited "ground-truth metadata" wording
   can leak evaluation context to officer-facing demo views.
6. M4 is deliberately sample-ID-driven synthetic evidence, so it is a pipeline
   demonstration rather than a detector for arbitrary uploads.

## 17. Recommended Next Milestones

1. **M14 — Firebase Infrastructure & Persistence:** design Auth verification,
   Firestore schema/rules, Storage references, audit records, retention, and
   migration from local upload/session and in-memory history.
2. **M14.5 — Officer-facing contract completion:** remove synthetic outcome
   labels/ground-truth wording from officer views and connect the frontend to
   the existing M11 result contract and persisted history.
3. **M15 — AI-Assisted Risk Reasoning:** add a bounded, structured-evidence-only
   advisory boundary with deterministic fallback and no autonomous decision.
4. **M16 — AI-Assisted Explanation / Officer Communication:** present AI context
   alongside deterministic evidence, limitations, and explicit officer control.
5. Real dataset evaluation, deployment/hardening, and final SIH demo preparation.

## 18. Explicitly NOT Implemented Yet

- Firebase Authentication, Firebase Storage, and a complete production Firebase
  persistence design (a limited existing Firestore fallback is not this);
- external AI API or model;
- real production document datasets;
- production-grade face recognition;
- autonomous decision-making;
- real-world accuracy or fraud-detection claims.
