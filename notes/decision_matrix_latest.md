# Decision Matrix — AI Home CoPilot (2026-02-14 15:50)

**Status:** RUN #8 | **Version:** 1.0 | **Stabil:** ⚠️ Review offen

---

## Priorität P0 — Testing Suite v0.1

### Offene Frage: Vollständige Implementierung

| Option | Aufwand | Wert | Risiko |
|--------|---------|------|--------|
| **A: Minimal (nur Stub erweitern)** | Niedrig (~2h) | Mittel | Wenig Coverage |
| **B: Vollständig v0.1** | Mittel (1-2 Tage) | **Hoch** ⭐ | Verzögerung P1 |
| **C: Später nach P1/P2** | — | Niedrig | Tech Debt |

**Empfehlung:** **Option B** — Testing Suite v0.1 vollständig implementieren

**Begründung:**
- Reduziert Risiko vor Production-Rollout
- Bestehende Module (Core v0.4.x, HA Integration v0.6.x) sind reif für Verifikation
- Stub bereits vorhanden, nur Erweiterung nötig

**Tradeoff:**
- Verzögert TAG_SYSTEM v0.2 leicht
- Aber: stabilere Basis für alle weiteren Module

**Umsetzung:**
- `tests/` Verzeichnis mit pytest fixtures
- Focus: Candidate Poller, Repairs Workflow, Decision Sync
- Integration Tests gegen lokales HA (wenn verfügbar)

---

## Priorität P1 — TAG_SYSTEM v0.2

### Offene Frage: Sensor Inventory Integration

| Option | Ansatz | Komplexität | Datenschutz |
|--------|--------|-------------|-------------|
| **A: Nur metrische Sensoren** | Power/Temp/Humidity | Niedrig | ✅ |
| **B: Alle Entity-Sensoren** | Inkl. binary sensors | Mittel | ⚠️ |
| **C: Getrenntes Inventory** | Eigenes Schema | Hoch | ✅ |

**Empfehlung:** **Option A + B Hybrid** — Metrische + binäre Sensoren, keine Audio/Video

**Begründung:**
- Power/Temp sind Kern für Energy Module
- Binary Sensors (motion, contact) wichtig für Habitus-Zonen
- Audio/Video bleibt `private` (Privacy-first)

**Tradeoff:**
- Option C sauberer, aber höherer Initial-Aufwand
- Hybrid bedeutet Schema-Mischung → später Migration nötig

**Umsetzung:**
- Tag `aicp.kind.sensor` mit Facetten `metric.*`, `binary.*`
- Keine `sys.*` Tags für Sensor-Daten
- Energy Module nutzt `aicp.cap.power_metering` Tag

---

## Priorität P2 — Energy Module (BLOCKIERT)

### Status: Wartet auf P0 + P1

| Blocker | Abhängigkeit | Freigabe wenn... |
|---------|--------------|------------------|
| Testing Suite | P0 | Testing Suite v0.1 stabil |
| TAG_SYSTEM | P1 | Sensor Inventory entschieden |

**Empfehlung:** **P2 pausieren** bis P0 + P1 abgeschlossen

**Begründung:**
- Energy Module erfordert klare Tag-Policies
- Ohne Testing: riskant für Production
- Kapazität: aktuell kein paralleles Arbeiten

---

## Zusammenfassung

| Priorität | Offene Frage | Empfehlung | Nächster Schritt |
|-----------|--------------|------------|------------------|
| **P0** | Testing Suite Umfang | B: Vollständig v0.1 | Implementierung starten |
| **P1** | Sensor Inventory | Hybrid (metric + binary) | Schema Entwurf |
| **P2** | Energy Module | Pausiert | Warten auf P0+P1 |

---

*Decision Matrix generiert: 2026-02-14 15:50 UTC+1*
*Worker: AI Home CoPilot Decision Matrix*
