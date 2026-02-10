# CHANGELOG_DEV (WIP)

Kurzliste von Änderungen im Branch `dev`, die noch nicht als Add-on Release getaggt sind.

- Stable Releases: `CHANGELOG.md` (Tags `copilot_core-vX.Y.Z`).

## Candidate: v0.4.4 (Candidates System - Automation Pattern Detection)

### 🤖 Candidates Module — AI-Driven Automation Discovery (2026-02-10)

**Core System**
- **`CandidateService`** (`copilot_core/candidates/service.py`): Main orchestration service for automation candidate detection and lifecycle management. Integrates with brain graph for pattern analysis.
- **`PatternDetector`** (`copilot_core/candidates/detector.py`): Privacy-first pattern detection from brain graph analysis. Four detection algorithms: temporal, trigger-response, zone coordination, and device following patterns.
- **`CandidateStore`** (`copilot_core/candidates/store.py`): Thread-safe SQLite storage with bounded capacity (1000 candidates), auto-pruning, and comprehensive filtering.
- **`Candidate Models`** (`copilot_core/candidates/models.py`): Privacy-bounded data models with evidence system (1KB metadata limits), blueprint generation, and deterministic IDs.

**REST API** (`/api/v1/candidates/`)
- Detection triggers: `POST /detection/trigger`, `GET /detection/status`
- Candidate management: `GET /`, `GET /{id}`, `POST /{id}/accept`, `POST /{id}/dismiss`
- Analytics: `GET /high-confidence`, `GET /stats`
- Maintenance: `POST /maintenance/prune`, bulk operations

**Testing & Quality**
- 47 comprehensive unit tests covering all components
- Privacy validation (metadata bounds, PII redaction, deterministic IDs)
- Performance validation (bounded memory, efficient queries, thread safety)
- Integrated into main.py with brain graph dependency injection

**Detection Algorithms**
1. **Temporal Patterns**: Recurring time-based activations (daily schedules)
2. **Trigger-Response**: State change → service call correlations within time windows
3. **Zone Coordination**: Device co-activation patterns within areas/zones
4. **Device Following**: Sequential device activations (light coordination)

**Privacy-First Design**
- No PII stored in candidates (anonymized patterns only)
- Bounded evidence metadata (1KB per evidence item)
- Deterministic candidate IDs for deduplication
- Configurable confidence thresholds and frequency requirements

## Previously Released: v0.4.3 (Dev Surface Observability)

### Dev Surface Module — Structured Logging & System Health (2026-02-10)
- **`DevSurfaceService`** (`copilot_core/dev_surface/service.py`): Central observability service with structured logging, error tracking, and system health monitoring.
- **Ring buffer logging** with configurable limits (default: 500 entries), level filtering (DEBUG/INFO/WARN/ERROR), and persistent JSONL file storage.
- **Error tracking**: automatic counting by exception type, most frequent error detection, last error capture with stack traces.
- **System health snapshots**: memory usage (via psutil), Brain Graph metrics (nodes/edges), events processed (24h), error rates, overall status (healthy/degraded/error).
- **REST API** endpoints at `/api/v1/dev/*`: `/logs`, `/errors`, `/health`, `/diagnostics`, `/clear` — all token-protected.
- **Integrated with Event Processor**: automatic logging of processing events, errors isolated from main pipeline.
- **10 comprehensive unit tests** covering all logging levels, error tracking, ring buffer limits, level filtering, file persistence, system health, diagnostics export.
- **Dependencies**: Added `psutil==6.1.0` to Dockerfile for memory monitoring.
- **Non-intrusive**: All logging is best-effort; failures never break main application flow.

## Released: v0.4.2 (Event Processing Pipeline)

### EventProcessor — EventStore → BrainGraph (2026-02-10)
- **`EventProcessor`** (`copilot_core/ingest/event_processor.py`): Bridges event ingest with Brain Graph service. Processes ingested events in real-time to build the knowledge graph.
- **State changes** → create/update entity + zone nodes, link entities to zones via `located_in` edges.
- **Service calls** → create service nodes, link to target entities via `targets` edges. Higher salience boost (0.8) for intentional actions vs. passive state changes (0.5).
- **Post-ingest callback** in `events_ingest.py`: Non-blocking hook fires after each accepted batch. Exceptions are logged but never fail the HTTP response.
- **EventStore.ingest_batch** now returns `accepted_events` for downstream consumers.
- **Extensible**: `add_processor()` allows plugging additional consumers (Mood Engine, Anomaly Detection, etc.).
- **11 unit tests** covering entity creation, zone linking, service→entity targeting, batch processing, error isolation, custom processor registration.
- **Total test count**: 76 unit tests across all Core modules (model: 8, store: 7, service: 10, tag registry, event store: 19, event processor: 11) ✓.

## Released: v0.4.1 (Brain Graph Module)

### Brain Graph Module (2026-02-10)
- **`/api/v1/graph/state`**: JSON API for bounded graph state with filtering (kind, domain, center/hops, limits).
- **`/api/v1/graph/snapshot.svg`**: DOT/SVG visualization with themes (light/dark), layouts (dot/neato/fdp), and hard render limits.
- **`/api/v1/graph/stats`**: Graph statistics + configuration (node/edge counts, limits, decay parameters).
- **`/api/v1/graph/prune`**: Manual pruning trigger.
- **`BrainGraphService`** (`copilot_core/brain_graph/service.py`): High-level graph operations with touch_node/touch_edge/link primitives, exponential decay, and HA event processing hooks.
- **`GraphStore`** (`copilot_core/brain_graph/store.py`): SQLite-backed storage with bounded capacity (default: 500 nodes, 1500 edges), automatic pruning, neighborhood queries, and cascading deletes.
- **`GraphNode`/`GraphEdge`** (`copilot_core/brain_graph/model.py`): Privacy-first data models with PII redaction, bounded metadata (2KB max), and effective score/weight calculation with decay.
- **`GraphRenderer`** (`copilot_core/brain_graph/render.py`): DOT/SVG generation with Graphviz integration, theme support, and error fallbacks.
- **27 unit tests** (model, store, service) covering privacy, bounds, decay, pruning, neighborhood queries, and HA event processing ✓.
- **Dependencies:** Added `graphviz` package to Dockerfile for SVG rendering.
- This establishes the central knowledge representation for entity/zone/device relationships with privacy-first design and automatic salience management.

**Breaking Changes:** None  
**Migration:** No config changes required, new endpoints accessible immediately  
**Tests:** ✅ All tests passing (compile + 27 brain graph tests)  
**Security:** PII redaction, bounded storage, no external calls

---

## Previous Release: v0.4.0

### Brain Graph Module (2026-02-10)
- **`/api/v1/graph/state`**: JSON API for bounded graph state with filtering (kind, domain, center/hops, limits).
- **`/api/v1/graph/snapshot.svg`**: DOT/SVG visualization with themes (light/dark), layouts (dot/neato/fdp), and hard render limits.
- **`/api/v1/graph/stats`**: Graph statistics + configuration (node/edge counts, limits, decay parameters).
- **`/api/v1/graph/prune`**: Manual pruning trigger.
- **`BrainGraphService`** (`copilot_core/brain_graph/service.py`): High-level graph operations with touch_node/touch_edge/link primitives, exponential decay, and HA event processing hooks.
- **`GraphStore`** (`copilot_core/brain_graph/store.py`): SQLite-backed storage with bounded capacity (default: 500 nodes, 1500 edges), automatic pruning, neighborhood queries, and cascading deletes.
- **`GraphNode`/`GraphEdge`** (`copilot_core/brain_graph/model.py`): Privacy-first data models with PII redaction, bounded metadata (2KB max), and effective score/weight calculation with decay.
- **`GraphRenderer`** (`copilot_core/brain_graph/render.py`): DOT/SVG generation with Graphviz integration, theme support, and error fallbacks.
- **27 unit tests** (model, store, service) covering privacy, bounds, decay, pruning, neighborhood queries, and HA event processing ✓.
- **Dependencies:** Added `graphviz` package to Dockerfile for SVG rendering.
- This establishes the central knowledge representation for entity/zone/device relationships with privacy-first design and automatic salience management.

### Event Ingest Endpoint (2026-02-10)
- **`POST /api/v1/events`**: Receives batched event envelopes from HA Events Forwarder. Validates schema, deduplicates (TTL-based), normalizes both current forwarder format and N3-spec envelope format.
- **`GET /api/v1/events`**: Query stored events with filters (domain, entity_id, zone_id, kind, since, limit).
- **`GET /api/v1/events/stats`**: Store diagnostics (buffer size, accepted/rejected/deduped totals).
- **`EventStore`** (`copilot_core/ingest/event_store.py`): Thread-safe bounded ring buffer + JSONL persistence. Privacy-first: validates source allowlist, truncates context IDs to 12 chars.
- **19 unit tests** (validation, ingest, dedup, query, normalization) all passing ✓.
- This completes the HA→Core data pipeline: Forwarder (HA) → Ingest (Core) → Store (ring buffer + JSONL).

### Candidate: v0.4.0-rc.1 (Tag System v0.1 Beta)
**Status:** Release-ready for approval (all tests passing, code-complete, awaiting explicit go-ahead).

#### Added
- **Tag System Module (`copilot_core/tagging/`):** Complete privacy-first tag registry scaffolding.
  - `tag_registry.py`: YAML-based canonical tag definitions with i18n support + alias validation.
  - `assignments.py`: Persisted tag-assignment store (JSON-backed) with CRUD operations, subject-kind validation, and filtered list/upsert.
  - Default tags: `aicp.kind.light`, `aicp.role.safety_critical`, `aicp.state.needs_repair`, `sys.debug.no_export`.
  - Configurable store path via `COPILOT_TAG_ASSIGNMENTS_PATH` env var.

- **Tag System API (`/api/v1/tag-system`):** Production-ready HTTP endpoints.
  - `GET /api/v1/tag-system/tags`: Canonical registry (language-aware, translation opt-in via query).
  - `GET /api/v1/tag-system/assignments`: Filtered assignments (by subject/tag/materialized status + limit).
  - `POST /api/v1/tag-system/assignments`: Upsert assignment with validation + tag-registry checks.

- **Shared Auth Helper (`copilot_core/api/security.py`):** Reusable JWT token validation.

#### Tests
- `test_tag_registry.py`: Registry loader + serializer + reserved-namespace validation.
- `test_tag_assignment_store.py`: Persisted store CRUD, validation, filtering, pruning.
- Both Core test suites **passing** ✓.
- HA integration test scaffolding ready (`test_tag_utils.py`, `test_tag_sync_integration.py`).

#### Security
- No raw HA attributes stored; only whitelisted scalars in assignment metadata.
- Subject kinds restricted to: `entity`, `device`, `area`, `automation`, `scene`, `script`, `helper`.
- Learned/candidate tags are `pending` by default (no materialization without explicit confirmation).

#### Breaking Changes
- None (new module).

#### Notes
- Integration tests for HA label materialization require full HA test runner (pytest + HA framework).
- Release recommended when HA integration is fully tested in CI.

### In Arbeit
- Forwarder Event Schema (Worker N3 report): minimal stable envelope, attribute projections, redaction policy, implementation checklist.
