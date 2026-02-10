# CHANGELOG - Home Assistant CoPilot Core Add-on

## [0.4.5] - 2026-02-10

### 🏷️ Tag System REST API - DELETE Operations

Completes CRUD functionality for tag assignment management with deletion endpoints.

#### Added
- **Assignment Deletion** (`/api/v1/tag-system/assignments/<id>`): 
  - `DELETE` endpoint for removing individual tag assignments
  - Returns 404 if assignment not found, 200 with deletion confirmation if successful
  - Privacy-safe: only deletes by exact assignment ID

- **Batch Assignment Deletion** (`/api/v1/tag-system/assignments/batch`):
  - `DELETE` endpoint for bulk removal of multiple assignments 
  - JSON payload: `{"assignment_ids": ["id1", "id2", ...]}`
  - Returns detailed statistics: requested count, actual deletions, not found count
  - Bounded operations: maximum 1000 assignment IDs per batch request
  - Resilient: partial success allowed (deletes existing, reports missing)

#### Enhanced
- **Complete CRUD**: Tag assignment API now supports full Create, Read, Update, Delete operations
- **Test Coverage**: Comprehensive test suite for deletion scenarios including edge cases
- **Error Handling**: Proper HTTP status codes and descriptive error messages

#### Technical
- Leverages existing `TagAssignmentStore.remove()` method for thread-safe deletion
- Maintains data integrity and atomicity for batch operations
- Consistent API patterns with existing endpoints (auth, error format, response structure)

This completes the tag assignment management API, enabling full lifecycle control for AI-driven tagging workflows.

## [0.4.4] - 2026-02-10

### 🤖 Candidates System - AI-Driven Automation Discovery

Introduces comprehensive automation candidate detection and management system based on brain graph pattern analysis.

#### Added
- **Candidate Detection Service** (`CandidateService`): Main orchestration for automation pattern detection
  - Privacy-first pattern detection from brain graph analysis
  - Four detection algorithms: temporal, trigger-response, zone coordination, device following
  - Configurable confidence thresholds and frequency requirements
  - Bounded storage with auto-pruning (1000 candidate limit)

- **Pattern Detection** (`PatternDetector`):
  - **Temporal Patterns**: Recurring time-based activations (daily schedules)
  - **Trigger-Response**: State change → service call correlations within time windows  
  - **Zone Coordination**: Device co-activation patterns within areas/zones
  - **Device Following**: Sequential device activations (light coordination)

- **REST API** (`/api/v1/candidates/`):
  - Detection triggers: `POST /detection/trigger`, `GET /detection/status`
  - Candidate management: `GET /`, `GET /{id}`, `POST /{id}/accept`, `POST /{id}/dismiss`
  - Analytics: `GET /high-confidence`, `GET /stats`
  - Maintenance: `POST /maintenance/prune`, bulk operations

- **Storage System** (`CandidateStore`):
  - Thread-safe SQLite storage with bounded capacity
  - Comprehensive filtering and query capabilities
  - Deterministic candidate IDs for deduplication
  - Automatic pruning of old dismissed candidates

#### Privacy & Security
- No PII stored in candidates (anonymized patterns only)
- Bounded evidence metadata (1KB per evidence item)
- Deterministic candidate IDs for stable deduplication
- Privacy-bounded data models with automatic redaction

#### Testing
- 47 comprehensive unit tests covering all components
- Privacy validation (metadata bounds, PII redaction)
- Performance validation (bounded memory, efficient queries, thread safety)
- Integrated into main.py with proper dependency injection

## [0.4.3] - 2026-02-10

### 📊 Dev Surface - Structured Logging & System Health

Added comprehensive observability and development tooling for Core system monitoring.

#### Added
- **Dev Surface Service** (`DevSurfaceService`): Central observability with structured logging
  - Ring buffer logging with configurable limits (500 entries default)
  - Level filtering (DEBUG/INFO/WARN/ERROR) and persistent JSONL storage
  - Error tracking with automatic counting by exception type
  - System health snapshots with memory usage and Brain Graph metrics

- **REST API** (`/api/v1/dev/`):
  - `/logs` - Structured log retrieval with filtering
  - `/errors` - Error statistics and most frequent errors
  - `/health` - System health status (healthy/degraded/error)
  - `/diagnostics` - Complete system diagnostics export
  - `/clear` - Log and error state reset

- **Integration**:
  - Automatic logging of Event Processor activities
  - Error isolation from main processing pipeline
  - Memory and performance monitoring via psutil

#### Testing
- 10 comprehensive unit tests covering all logging functionality
- Performance validation for ring buffer and level filtering
- Health monitoring and diagnostics export validation

## [0.4.2] - 2026-02-09

### 🧠 Brain Graph Core Module

Privacy-first knowledge graph system for entity relationships and pattern detection.

#### Added
- **Brain Graph Service** (`BrainGraphService`): Core knowledge graph with bounded storage
  - Maximum 500 nodes, 1500 edges with automatic pruning
  - Exponential decay scoring (24h half-life nodes, 12h edges)
  - Privacy-first design with automatic PII redaction
  - SQLite persistence with transaction support

- **REST API** (`/api/v1/graph/`):
  - `/state` - Complete graph export (nodes + edges)
  - `/stats` - Node/edge counts and memory usage
  - `/snapshot.svg` - Visual graph representation
  - Node/edge CRUD operations with privacy validation

- **Privacy Features**:
  - Automatic redaction of sensitive data (GPS, tokens, URLs)
  - Bounded node storage prevents memory bloat
  - No long-term storage of raw event data

#### Testing
- 23 unit tests covering graph operations and privacy
- Memory boundary validation
- Privacy redaction verification

## [0.4.1] - 2026-02-08

### 🔄 Event Processing Pipeline

Core event ingestion and processing system for Home Assistant integration.

#### Added
- **Event Processor** (`EventProcessorService`): Handles incoming HA events
  - Schema validation for envelope format v1
  - Deduplication with TTL-based cleanup (24h default)
  - Privacy-first processing with sensitive data redaction
  - Metrics and health monitoring

- **REST API** (`/api/v1/events/`):
  - `POST /ingest` - Event ingestion endpoint
  - `GET /stats` - Processing statistics
  - `GET /health` - Pipeline health status

- **Core Infrastructure**:
  - SQLite-based deduplication store
  - Configurable batch processing
  - Error handling and recovery mechanisms

## [0.4.0] - 2026-02-08

### 🎉 Initial MVP Release

First functional release of CoPilot Core with basic API framework.

#### Added
- **Core Service Framework**: Basic FastAPI application structure
- **Health Endpoints**: `/health`, `/version` for monitoring
- **Authentication**: Token-based API protection
- **Configuration**: Home Assistant Add-on integration
- **Docker Support**: Multi-architecture builds (amd64, aarch64)

#### Infrastructure
- Home Assistant Add-on configuration with ingress support
- Structured logging with configurable levels
- Basic error handling and service lifecycle management

---

**Installation**: Available through Home Assistant Community Store (HACS)  
**Repository**: https://github.com/GreenhillEfka/Home-Assistant-Copilot  
**Documentation**: https://docs.openclaw.ai  