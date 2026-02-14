# Debug Level Worker Report
Generated: 2026-02-14 1:15 PM (Europe/Berlin)

---

## 1. Ist-Zustand (Update)

### ✅ Bereits Implementiert

**HA Integration (ai_home_copilot_hacs_repo):**

| Feature | Status | Location |
|---------|--------|----------|
| Debug Enable (30min Button) | ✅ | `button.py:CopilotEnableDebug30mButton` |
| Debug Disable Button | ✅ | `button.py:CopilotDisableDebugButton` |
| Clear Error Digest Button | ✅ | `button.py:CopilotClearErrorDigestButton` |
| Services (enable/disebug/clear) | ✅ | `core/modules/dev_surface.py` |
| Kernel State (devlog, errors, debug) | ✅ | `core/modules/dev_surface.py:_get_kernel()` |
| DevLogBuffer + ErrorDigest | ✅ | `core/modules/dev_surface.py` |
| OptionsFlow (devlog_push) | ✅ | `config_flow.py` |
| Diagnostics Export | ✅ | `diagnostics.py` |

**Core Add-on (ha-copilot-repo):**

| Feature | Status | Location |
|---------|--------|----------|
| DevSurfaceService | ✅ | `copilot_core/dev_surface/service.py` |
| Ring Buffer (500 Einträge) | ✅ | `service.py:DevSurfaceService` |
| Log Persistence (`/data/dev_logs.jsonl`) | ✅ | `service.py` |
| API Endpoints (logs, errors, health) | ✅ | `copilot_core/dev_surface/api.py` |
| Error Summary + System Health | ✅ | `service.py` |

### ⚠️ Noch Offen (aus letztem Report)

| Feature | Priorität | Status |
|---------|-----------|--------|
| **Select-Entity: Diagnostic Mode** | Kurzfristig | ❌ Fehlt |
| **Clear All Logs Button** | Kurzfristig | ❌ Fehlt |
| **Log-Level Dropdown (OptionsFlow)** | Mittelfristig | ❌ Fehlt |
| **Copy Diagnostics Button** | Mittelfristig | ❌ Fehlt |
| **HA Logger Integration** | Langfristig | ❌ Fehlt |

---

## 2. Repo-Status

### ai_home_copilot_hacs_repo
```
Branch: main
Status: Uncommitted changes in docs/PROJECT_PLAN.md
Letzter Commit: 46b7924 (🧪 Option C: HA Integration Test Suite v0.5.8)
```

### ha-copilot-repo
```
Branch: release/v0.4.1
Status: Clean working tree
Letzter Commit: 98dd7b2 (Energy Neuron v0.4.11)
```

---

## 3. Empfohlene Tasks (dieser Run)

### Task 1: Select-Entity für Diagnostic Mode
```
File: custom_components/ai_home_copilot/select.py
File: custom_components/ai_home_copilot/const.py (CONF_DIAGNOSTIC_MODE)
File: custom_components/ai_home_copilot/config_flow.py (OptionsFlow)

Options:
- "off" (default)
- "light" (INFO+)
- "full" (DEBUG, 30min auto-disable)

Erwarteter Aufwand: ~2h
```

### Task 2: Clear All Logs Button
```
File: custom_components/ai_home_copilot/button.py (CopilotClearAllLogsButton)
Backend: POST /api/v1/dev/clear + DevLogBuffer.clear()

Erwarteter Aufwand: ~1h
```

---

## 4. Offene Fragen (unchanged)

1. **Mode-Naming:** "Diagnostic Mode" vs "Debug Level" vs "Verbosity"?
2. **Default-Level:** INFO oder WARN für Production?
3. **Timer-Länge:** 15min, 30min, oder einstellbar?
4. **Persistenz:** Im RAM (current) oder in Options (restart-sicher)?
5. **UI-Vorschau:** Soll PilotSuite den aktuellen Mode anzeigen?

---

## 5. Quick Wins (falls Zeit)

- **Documentation:** `docs/debug_mode_guide.md` erstellen
- **Test Coverage:** Unit-Tests für `DevSurfaceModule` erweitern
- **Error Registry:** Neue Error-Codes für häufige Fehler hinzufügen

---

*Report generiert von Debug Level Worker (cron:f84e4b7d-c40f-46b3-8dad-ba598e15ccf5)*
