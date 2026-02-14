# Debug Level Worker Report
Generated: 2026-02-14 1:45 PM (Europe/Berlin)

---

## 1. Ist-Zustand (keine Änderungen seit letztem Run)

### ✅ Bereits Implementiert

**HA Integration (ai_home_copilot_hacs_repo):**

| Feature | Status | Location |
|---------|--------|----------|
| Debug Enable (30min Button) | ✅ | `button.py:CopilotEnableDebug30mButton` (L796) |
| Debug Disable Button | ✅ | `button.py:CopilotDisableDebugButton` (L823) |
| Clear Error Digest Button | ✅ | `button.py:CopilotClearErrorDigestButton` (L850) |
| Services (enable/disable/clear) | ✅ | `core/modules/dev_surface.py` |
| Kernel State (devlog, errors, debug) | ✅ | `core/modules/dev_surface.py:_get_kernel()` |
| DevLogBuffer + ErrorDigest | ✅ | `core/modules/dev_surface.py` |
| OptionsFlow (devlog_push) | ✅ | `config_flow.py` (L396+) |
| Diagnostics Export | ✅ | `diagnostics.py` |
| Select-Entities (Media Context) | ✅ | `select.py` (Zone, ManualTarget) |

**Core Add-on (ha-copilot-repo):**

| Feature | Status | Location |
|---------|--------|----------|
| DevSurfaceService | ✅ | `copilot_core/dev_surface/service.py` |
| Ring Buffer (500 Einträge) | ✅ | `service.py` |
| Log Persistence (`/data/dev_logs.jsonl`) | ✅ | `service.py` |
| API Endpoints (logs, errors, health) | ✅ | `copilot_core/dev_surface/api.py` |
| Error Summary + System Health | ✅ | `service.py` |

### ⚠️ Noch Offen

| Feature | Priorität | Aufwand | Status |
|---------|-----------|---------|--------|
| **Select-Entity: Diagnostic Mode** | Kurzfristig | ~2h | ❌ Fehlt |
| **Clear All Logs Button** | Kurzfristig | ~1h | ❌ Fehlt |
| **Log-Level Dropdown (OptionsFlow)** | Mittelfristig | ~2h | ❌ Fehlt |
| **Copy Diagnostics Button** | Mittelfristig | ~1h | ❌ Fehlt |
| **HA Logger Integration** | Langfristig | ~3h | ❌ Fehlt |

---

## 2. Repo-Status (unverändert)

### ai_home_copilot_hacs_repo
```
Branch: main
Uncommitted: docs/PROJECT_PLAN.md (modified)
HEAD: 46b7924 — 🧪 Option C: HA Integration Test Suite (v0.5.8)
```

### ha-copilot-repo
```
Branch: release/v0.4.1
Status: Clean
HEAD: 00eed6e — feat: Brain Graph configurable limits (v0.4.12)
```

---

## 3. Analyse: Nächster sinnvoller Schritt

### Empfehlung: **Diagnostic Mode Select-Entity** (Top-Priorität)

**Warum:** Die vorhandenen Debug-Buttons sind binär (an/aus). Ein Select-Entity mit Stufen (`off` / `light` / `full`) gibt dem User feinere Kontrolle und ist in HA-Dashboards nativ darstellbar.

**Implementierungsplan:**

1. **`const.py`** — Neue Konstanten:
   ```python
   CONF_DIAGNOSTIC_MODE = "diagnostic_mode"
   DIAGNOSTIC_MODES = ["off", "light", "full"]
   ```

2. **`select.py`** — Neue `DiagnosticModeSelectEntity`:
   - Options: `off`, `light` (INFO+), `full` (DEBUG, auto-disable nach Timer)
   - Liest/schreibt DevSurface-State via Coordinator
   - `full` triggert bestehende 30min-Timer-Logik

3. **`select.py:async_setup_entry`** — Entity registrieren (neben Media-Selects)

4. **`config_flow.py`** — Optional: Default-Mode in OptionsFlow

**Abhängigkeiten:** Keine — bestehende DevSurface-Infrastruktur reicht.

### Zweit-Empfehlung: **Clear All Logs Button**

Trivial: Neuer `CopilotClearAllLogsButton` in `button.py`, ruft DevSurface `.clear_all()` auf.

---

## 4. Offene Fragen (an User)

1. **Mode-Naming:** "Diagnostic Mode" vs "Debug Level" vs "Verbosity"?
2. **Default-Level:** `off` oder `light` (INFO) für Production?
3. **Auto-Disable Timer:** Fix 30min oder konfigurierbar (15/30/60)?
4. **Persistenz:** RAM-only (current) oder restart-sicher (Options)?
5. **PilotSuite:** Soll der aktuelle Mode dort angezeigt werden?

---

## 5. Status

**Keine neuen Tasks im Command-File.** Repos unverändert seit 12:45.
Nächster Run: ~2:15 PM. Bei Tasks → `notes/debug_level_worker_command.md` beschreiben.

---

*Worker: cron:f84e4b7d-c40f-46b3-8dad-ba598e15ccf5 | Lauf 3 (14.02.2026)*
