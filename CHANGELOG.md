# CHANGELOG - Home Assistant CoPilot Core Add-on

## [0.4.9] - 2026-02-10

### 🧠 Brain Dashboard Summary API (N4 Enhancement)

Enhanced Brain Graph dev surface with comprehensive dashboard endpoints for HA Integration display.

#### Added
- **Brain Dashboard Summary API** (`/api/v1/dashboard/brain-summary`):
  - Consolidated health metrics: brain graph stats, 24h activity, candidate detection
  - Health scoring algorithm (0-100) based on connectivity, activity level, system stability  
  - Actionable recommendations for optimizing brain graph data collection
  - Top entity activity tracking and trend analysis
- **Quick Graph API** (`/api/v1/dashboard/quick-graph.svg`):
  - Dashboard-optimized brain graph visualizations (small/medium/large sizes)
  - Simplified rendering for embedded display in HA dashboards (20-80 nodes max)

#### Enhanced
- **N4 PROJECT_PLAN advancement** - Brain Graph dev surface now includes dashboard APIs
- **Graceful degradation** in dashboard endpoints when services are unavailable
- **Activity metrics** - 24-hour event and entity tracking for comprehensive health assessment

#### Technical Implementation
- Dashboard API integrates seamlessly with BrainGraphService, CandidateService, EventStore
- Health score considers graph connectivity (edges/nodes ratio), recent activity, system stability
- Size-specific rendering limits for dashboard widgets optimize performance

#### Privacy & Performance
- Dashboard data is aggregated and anonymized - no raw entity data exposure
- Configurable rendering limits prevent resource exhaustion
- All endpoints require API key authentication

#### Quality Assurance
- ✅ Full py_compile validation across all new modules
- ✅ Backwards compatible with existing Brain Graph API endpoints  
- ✅ Error handling with informative SVG fallbacks for rendering issues
- ✅ Integration with existing API security framework

## [0.4.8] - 2026-02-10

### 🔍 Capabilities Discovery Endpoint (N3 Step Complete)

Implementation of Core Add-on capabilities discovery for seamless HA Integration compatibility checking.

#### Added
- **Capabilities Endpoint** (`/api/v1/capabilities`):
  - Core version and API compatibility information
  - Feature flags for all supported capabilities
  - Health indicators (uptime, last event, total processed events)
  - Integration hints (batch sizes, supported domains, privacy domains)
  - No authentication required for discovery
  
#### Features Reported
- ✅ **Event envelope v1** - Privacy-first event processing
- ✅ **Privacy redaction** - PII and sensitive data filtering  
- ✅ **Zone enrichment** - Entity→zone mapping
- ✅ **Candidate lifecycle** - Full suggestion management
- ✅ **Brain Graph** - Activity correlation and visualization
- ✅ **Habitus mining** - Habit detection from event patterns
- 🚫 **Mood ranking** - Planned future feature
- 🚫 **Energy analysis** - Planned future feature

#### Integration Benefits
- HA Integration can verify Core is reachable and healthy
- Automatic feature detection prevents compatibility issues
- Clear indicators of what data processing capabilities are active
- Supports graceful degradation when Core Add-on is offline

This completes the **N3 PROJECT_PLAN step**: "Capabilities ping and clear 'Core supports v1?' status"

## [0.4.7] - 2026-02-10

### 🔒 Privacy-First Event Envelope System

Complete implementation of Alpha Worker n3_forwarder_quality specification for stable, privacy-first event processing.

#### Added
- **EventEnvelope Processor** (`envelope.py`):
  - Schema versioning with v=1 stable envelope format
  - Privacy-first PII redaction (emails, IPs, phone numbers, URLs, GPS coords)
  - Domain-specific attribute projection (light, climate, media_player, etc.)
  - Context ID truncation (12 chars) for correlation without reversibility
  - Zone enrichment support with configurable entity→zone mapping

- **Enhanced Event Pipeline**:
  - All events now normalized through envelope before BrainGraph processing
  - Raw HA events never reach Core modules (decoupled from HA internals)
  - Comprehensive test suite validates Alpha Worker specification compliance
  - Better error tracking with normalization/filtering statistics

#### Privacy & Security Improvements
- **Always Redact**: `user_id`, `entity_picture`, `latitude`/`longitude`, tokens
- **Attribute Filtering**: Only actionable attributes forwarded per domain
- **Trigger Inference**: User/automation/unknown classification from context
- **Bounded Metadata**: Max field sizes prevent data leaks

#### Technical Details
- **Breaking**: Events now use normalized envelope schema
- **Backward Compatible**: v=1 schema supports evolution
- **Zero Config**: Works out-of-box with sensible defaults
- **Extensible**: Easy to add new domains and redaction rules

Integration with existing Brain Graph, Tag System, and Automation Candidates unchanged.

## [0.4.6] - 2026-02-10

### 📚 Brain Graph API Documentation & Capabilities

Comprehensive documentation and capability announcement for the privacy-first knowledge graph system.

#### Added
- **Complete API Documentation** (`docs/brain_graph_api.md`):
  - All REST endpoints: `/state`, `/snapshot`, `/stats`, `/prune`
  - Data models: `GraphNode`, `GraphEdge` with full schemas
  - Privacy & security features: automatic PII redaction, bounded storage
  - Integration patterns: Event processing, Tag System, Automation Candidates
  - Troubleshooting guide and configuration reference

- **Enhanced README**: Updated with current system capabilities
  - Brain Graph System: Privacy-first knowledge graph (500 nodes, 1500 edges)
  - Tag System: AI-driven entity classification with CRUD API
  - Automation Candidates: ML-based automation discovery
  - Complete API endpoint reference

#### Technical Foundation
- **Privacy-First Design**: No raw HA attributes, automatic redaction patterns
- **Bounded Architecture**: Configurable limits prevent resource exhaustion  
- **Time Decay Model**: Exponential decay with 24h/12h half-life for nodes/edges
- **Real-time Visualization**: SVG graph snapshots for operational insight
- **Thread-Safe Operations**: Concurrent read/write support with SQLite backend

#### Integration Ready
- Brain Graph APIs fully documented for external tool integration
- Establishes foundation for advanced AI automation workflows
- Clear data models enable predictable graph interactions

This release makes the Brain Graph system's capabilities transparent and accessible, completing the foundational documentation for the AI Home CoPilot's knowledge representation layer.

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