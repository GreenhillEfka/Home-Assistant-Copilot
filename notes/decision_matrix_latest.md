# Decision Matrix — AI Home CoPilot

**Letzte Aktualisierung:** 2026-02-14 12:50  
**Run:** 5 | **Offene Entscheidungen:** 3

---

## 1. Nächstes Implementierungs-Ziel

### Option A: SystemHealth Modul
- **Aufwand:** Niedrig (~1 Woche)
- **Scope:** DB/Recorder-Checks, Entity-Bloat, Top-Talkers
- **Abhängigkeiten:** HA Recorder API, keine externen Systeme

### Option B: Energy Modul  
- **Aufwand:** Mittel-Hoch (~2-3 Wochen)
- **Scope:** Baseload, Anomalien, PV-Shifting, Explainability
- **Abhängigkeiten:** Braucht konkrete Sensor-Konfiguration (offene Fragen)

### Option C: HA Integration Testing Suite ⭐ **EMPFOHLEN**
- **Aufwand:** Niedrig-Mittel
- **Scope:** Repairs workflow, Candidate Poller, Decision Sync
- **Wert:** Gibt Vertrauen für Production-Deployment

### Empfehlung: **Option C**

**Begründung:**
- Testing reduziert Risiko vor Production-Rollout
- Bestehende Module (Core v0.4.8, HA Integration v0.5.7) sind reif für Verifikation
- Keine Blockierung durch offene Spezifikationsfragen

**Risiko/Tradeoff:**
- Verzögert sichtbare Features (Health/Energy)
- Testing ist "unsichtbar" bis Issue auftritt

**Umsetzung:**
- `tests/test_repairs_workflow.py` → Mock HA Repairs API
- `tests/test_candidate_poller.py` → Polling-Cycle-Tests
- `tests/test_decision_sync.py` → Core ↔ Integration Sync-Tests
- Siehe: `/config/.openclaw/workspace/docs/module_specs/`

---

## 2. TAG_SYSTEM v0.2 — Offene Punkte

### Frage 2a: Label-Sync Objektarten
**Option A:** Nur Entities/Devices/Areas (Conservative)
- Pro: Minimal, weniger Komplexität
- Contra: Automationen/Skripte können Labels nicht nutzen

**Option B:** Alle unterstützten HA-Label-Typen (Full)
- Pro: Maximale Flexibilität
- Contra: Mehr Sync-Logik nötig

### Empfehlung: **Option B (Full)**

**Begründung:**
- HA Labels unterstützen bereits alle Typen
- Zukunftssicher für erweiterte Automationen
- Konsistent mit `subject.*` Registry-IDs

### Umsetzung:
- Sync für `automation`, `scene`, `script`, `helper` aktivieren
- Check in `tag_system_impl_v0.1.md` ergänzen
- Migrationspfad dokumentieren

---

### Frage 2b: Stable Subject Addressing
**Option A:** Registry-ID (`entity_id` oder `device_id`)
- Pro: Stabil, einzigartig
- Contra: Nicht alle Objekte haben Registry-ID (z.B. Areas)

**Option B:** Mix aus Registry-ID + Fallback
- Pro: Flexibel für alle Typen
- Contra: Komplexerer Lookup

**Option C:** HA-Label-UID als kanonische ID
- Pro: Einheitlich für alle Subjects
- Contra: Kann sich bei Label-Löschung ändern

### Empfehlung: **Option B (Mix + Fallback)**

**Begründung:**
- Area Registry existiert, hat IDs
- Automationen/Skripte/Scripte haben IDs
- `user.*` Tags könnten nur Label-basiert sein

### Umsetzung:
```yaml
# canonical_subject_id
- kind: entity      → entity_id (Registry)
- kind: device      → device_id (Registry)
- kind: area       → area_id (Registry)  
- kind: automation  → automation_id
- kind: script     → script_id
# ...
```

---

### Frage 2c: Learned Tags → HA-Labels
**Option A:** Nie automatisch (User Approval Required)
- Pro: Maximale Kontrolle, keine Überraschungen
- Contra: Träger Workflow

**Option B:** Automatisch bei Confidence > 0.9
- Pro: Schnellere Wertsteigerung
- Contra: Risiko falsch-positiver Labels

### Empfehlung: **Option A (Nie automatisch)**

**Begründung:**
- Privacy-first: Labels sind sichtbar/HA-nativ
- Learned Tags sind potenziell instabil
- Bessere UX: explizite Bestätigung buildet Vertrauen

### Umsetzung:
- In `tag_system_impl_v0.1.md`: `materialize_as_label: false` default für learned
- UI/CLI-Workflow: "Confirm as HA-Label" Button

---

## 3. ENERGY MODULE v0.1 — Offene Konfigurationsfragen

### Frage 3a: Verfügbare Sensoren
**Bitte beantworten:**
1. Haus-Summenleistung: `sensor.house_power` oder `sensor.grid_power`?
2. PV-Leistung: `sensor.pv_power` vorhanden?
3. Netzbezug/Export: separate Sensoren?
4. Batterie: `sensor.battery_power` + SOC?

### Empfehlung: **Muss User klären**

**Umsetzung:**
- Checkliste erstellen für HA Entity Inventory
- `energy_module.yaml` Konfiguration erst nach Klärung

---

### Frage 3b: Device-Level Power Sensors
**Option A:** Keine (nur Summen)
- Pro: Simpler
- Contra: Weniger Granularität für Anomalien

**Option B:** Smarte Steckdosen/Shelly/etc.
- Pro: Beste Anomalie-Erkennung
- Contra: Muss pro Device konfiguriert werden

### Empfehlung: **Option B (wenn vorhanden)**

**Umsetzung:**
- Inventory-Scan: Power-Sensoren finden
- Auto-Discovery für `energy_module.yaml`

---

### Frage 3c: Dynamische Strompreise?
**Option A:** Feste Offpeak-Zeiten (z.B. 22-06 Uhr)
- Pro: Einfach, kein externer API
- Contra: Weniger Optimierungspotenzial

**Option B:** API (Tibber, Awattar, etc.)
- Pro: Echtzeit-Optimierung
- Contra: External API nötig

### Empfehlung: **Option A (v0.1), Option B (v0.2)**

**Umsetzung:**
- v0.1: `input_select.tariff_period` oder `input_datetime`
- v0.2: API-Integration planen

---

## Action Items

| Priorität | Item | Status |
|-----------|------|--------|
| P0 | Testing Suite entscheiden | ⏳ User |
| P1 | TAG_SYSTEM Objektarten finalisieren | ⏳ User |
| P1 | TAG_SYSTEM Addressing-Schema implementieren | ⏳ User |
| P1 | Energy Sensor Inventory erheben | ⏳ User |
| P2 | SystemHealth Modul planen | ⏳ Blocked by P0 |
| P2 | UniFi Modul planen | ⏳ Blocked by P0 |
| P2 | Energy Module v0.1 finalisieren | ⏳ Blocked by P1-P3 |

---

*Generated by Decision Matrix Worker (Run #5)*
