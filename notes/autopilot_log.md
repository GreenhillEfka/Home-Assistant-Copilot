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
