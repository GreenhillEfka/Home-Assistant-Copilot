# AI Home CoPilot — Autopilot Log (10min loop)

Window: 2026-02-08 06:18–10:18 (Europe/Berlin)

This log is appended by the Autopilot cron.

---

## 2026-02-08 06:41 — Kickstart (manual)

### What changed
- Added **Tag-System v0.1 spec**: `docs/TAG_SYSTEM_v0.1.md` (privacy-first taxonomy + HA Labels mapping + governance + migration notes).
- Started tracking Autopilot/worker state & research notes under `notes/` (state, queue, reports, questions).
- Ignored local nested repo checkout: `ai_home_copilot_hacs_repo/` added to `.gitignore`.

### Status
- Not a release (docs/notes only). Changes committed on dev branch: `dev/autopilot-2026-02-08-0641`.

### Next logical step
- Decide whether Tag-System decisions in `docs/TAG_SYSTEM_v0.1.md` should be treated as **canonical** (and if yes, wire a minimal implementation stub in the HA integration or core add-on):
  - pick supported subject kinds for v0.1 (entity/device/area vs more),
  - decide `aicp.*` vs allowing `user.*`,
  - decide whether learned/candidate tags may ever materialize as HA labels (recommended: no).

---

## 2026-02-14 13:50 — Brain Graph Configurable Limits (autopilot)

### What changed
- **Config Integration**: Brain Graph module now supports runtime configuration via `config.json`
- Added configurable parameters with validation bounds:
  - `max_nodes` (100-5000, default: 500)
  - `max_edges` (300-15000, default: 1500)
  - `node_half_life_hours` (1-168h, default: 24.0)
  - `edge_half_life_hours` (1-168h, default: 12.0)
  - `node_min_score` (0.01-1.0, default: 0.1)
  - `edge_min_weight` (0.01-1.0, default: 0.1)
- Updated `core_setup.py` to accept optional `config` parameter
- Maintains backward compatibility (uses defaults if not specified)

### Files changed
- `addons/copilot_core/config.json` (+JSON schema, +options)
- `addons/copilot_core/rootfs/usr/src/app/copilot_core/core_setup.py` (+config parsing, +GraphStore init)
- `CHANGELOG.md` (+v0.4.12 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/Home-Assistant-Copilot/releases/tag/v0.4.12
- All py_compile checks passed
- Modules verified: UniFi (v0.1), Energy (v0.1), Brain Graph, Mood, Habitus, Candidates

### 2026-02-14 13:49 — UniFi + Energy Neurons Release (autopilot)

### What changed
- **UniFi Neuron v0.1** release: Network monitoring module
  - WAN status (uplink, latency, packet loss)
  - Client roaming events
  - Traffic baselines
  - REST API: `/api/v1/unifi/*`
- **Energy Neuron v0.1** release: Energy monitoring & optimization
  - Consumption/production monitoring
  - Anomaly detection (severity levels)
  - Load shifting opportunities
  - Explainability for suggestions
  - REST API: `/api/v1/energy/*`
- **Brain Graph Limits** (v0.4.12) already included

### Files changed
- `CHANGELOG.md` (+v0.4.10 UniFi, +v0.4.11 Energy, v0.4.12 Brain Graph Limits)
- `addons/copilot_core/config.json` (version: 0.4.12 → 0.4.13)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/Home-Assistant-Copilot/releases/tag/v0.4.13
- All modules compile (py_compile verified)
- UniFi + Energy Neurons now official releases

### Next logical step
- HA Integration module (HACS repo): Connect core neurons to HA entities/events
- Or: Implement Tag System CRUD API (pending user answers to 12 questions)
- Or: Weather integration for PV forecasting (energy follow-up)
