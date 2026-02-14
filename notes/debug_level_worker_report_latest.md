# Debug Level Worker Report
Generated: 2026-02-14 2:15 PM (Europe/Berlin)

---

## 1. Ist-Zustand

### ✅ Bereits Implementiert

**HA Integration (ai_home_copilot_hacs_repo):**

| Feature | Status | Location |
|---------|--------|----------|
| Debug Enable (30min Button) | ✅ | `button.py:CopilotEnableDebug30mButton` |
| Debug Disable Button | ✅ | `button.py:CopilotDisableDebugButton` |
| Clear Error Digest Button | ✅ | `button.py:CopilotClearErrorDigestButton` |
| Services (enable/disable/clear) | ✅ | `core/modules/dev_surface.py` |
| Kernel State (devlog, errors, debug) | ✅ | `core/modules/dev_surface.py` |
| DevLogBuffer + ErrorDigest | ✅ | `core/modules/dev_surface.py` |
| OptionsFlow (devlog_push) | ✅ | `config_flow.py` |
| Diagnostics Export | ✅ | `diagnostics.py` |
| PilotSuite Dashboard | ✅ | `pilotsuite_dashboard.py` |

**Core Add-on (ha-copilot-repo):**

| Feature | Status | Location |
|---------|--------|----------|
| DevSurfaceService | ✅ | `copilot_core/dev_surface/service.py` |
| Ring Buffer (500 Einträge) | ✅ | `service.py` |
| Log Persistence (`/data/dev_logs.jsonl`) | ✅ | `service.py` |
| API Endpoints (logs, errors, health) | ✅ | `copilot_core/dev_surface/api.py` |

### ⚠️ Noch Offen

| Feature | Priorität | Aufwand | Status |
|---------|-----------|---------|--------|
| **Diagnostic Mode Select-Entity** | Hoch | ~2h | ❌ Fehlt |
| **Clear All Logs Button** | Mittel | ~1h | ❌ Fehlt |
| **Log-Level Dropdown (OptionsFlow)** | Mittel | ~2h | ❌ Fehlt |
| **Copy Diagnostics Button** | Niedrig | ~1h | ❌ Fehlt |
| **HA Logger.set_level Integration** | Niedrig | ~3h | ❌ Fehlt |

---

## 2. Repo-Status

### ai_home_copilot_hacs_repo
```
Branch: main (clean)
HEAD: 159bd15 — ⚡ Energy Context Module
```

### ha-copilot-repo
```
Branch: release/v0.4.1 (clean)
HEAD: ec8e9d3 — feat: UniFi + Energy Neurons release (v0.4.13)
```

---

## 3. Analyse & Vorschläge

### Empfehlung 1: Diagnostic Mode Select-Entity (Top-Priorität)

**Warum:** Bietet feinere Kontrolle als binäre Buttons.

**Implementierung:**
1. Neue Konstanten in `const.py`:
   ```python
   DIAGNOSTIC_MODES = ["off", "light", "full"]
   ```
2. Neue `DiagnosticModeSelectEntity` in `select.py`
3. Integration in bestehende DevSurface-State-Maschine

### Empfehlung 2: Clear All Logs Button

Neuer `CopilotClearAllLogsButton` in `button.py`, trivial (~1h).

### Empfehlung 3: OptionsFlow Erweiterung

Log-Level Dropdown für persistentes Debugging über Neustarts hinweg.

---

## 4. Offene Fragen

1. **Mode-Naming:** "Diagnostic Mode" vs "Debug Level"?
2. **Persistenz:** RAM-only oder über Options persistieren?
3. **Auto-Disable:** Fix 30min oder konfigurierbar?

---

## 5. Status

**Keine Tasks im Command-File.** Repos sind clean.
Nächster Run: ~2:45 PM.

---

*Worker: cron:f84e4b7d-c40f-46b3-8dad-ba598e15ccf5 | Lauf 4 (14.02.2026)*
