# Home Assistant CoPilot - Core Add-on

This repository provides the **AI Home CoPilot Core Add-on** for Home Assistant, offering privacy-first AI automation capabilities.

## Install (Add-on repo)
Home Assistant → Settings → Add-ons → Add-on Store → ⋮ → Repositories → add this repo URL.

Then install: **AI Home CoPilot Core (MVP)**.

## Core Features (v0.4.5+)

### 🧠 Brain Graph System
Privacy-first knowledge graph maintaining relationships between HA entities, zones, and concepts:
- **Bounded storage**: 500 nodes, 1500 edges maximum
- **Time decay**: Automatic pruning with exponential decay
- **REST API**: Complete CRUD operations via `/api/v1/graph/*`
- **Visualization**: Real-time SVG graph snapshots
- **Privacy protection**: Automatic PII redaction, no raw HA attributes stored

### 🏷️ Tag System
AI-driven entity classification and management:
- **Auto-tagging**: Intelligent entity categorization
- **CRUD API**: Full tag assignment lifecycle via `/api/v1/tag-system/*`
- **Batch operations**: Efficient bulk tag management

### 🤖 Automation Candidates
AI-powered automation discovery from usage patterns:
- **Pattern detection**: Temporal, trigger-response, zone coordination
- **Confidence scoring**: ML-based automation recommendations
- **Safe suggestions**: Privacy-first pattern analysis

## API Endpoints
After install, the add-on provides REST APIs at `http://[host]:8099/api/v1/`:
- **Core**: `/health`, `/version`, `/metrics`
- **Brain Graph**: `/graph/state`, `/graph/snapshot`, `/graph/stats`, `/graph/prune`  
- **Tags**: `/tag-system/tags`, `/tag-system/assignments`
- **Candidates**: `/candidates/list`, `/candidates/generate`

See [docs/brain_graph_api.md](docs/brain_graph_api.md) for detailed API documentation.

## Channels
- Stable: GitHub Releases/Tags (recommended)
- Dev: opt-in branch builds

## Governance
No silent updates. Updates are explicit and should be logged as governance events in the CoPilot concept.
