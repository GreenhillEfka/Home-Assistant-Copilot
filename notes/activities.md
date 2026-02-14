
---

## 2026-02-14 18:58 - Core Add-on Project Agent

### Status: Habitus Zones v2 Architecture Review

**Sync-Status:**
- ✅ HA Integration: Zones v2 Store + Entities fertig
- ⚠️ Core Add-on Brain Graph: `zone:` Nodes + `in_zone` Edges vorhanden  
- ❌ Core Add-on Zone Management: Fehlt

**Analyse:**
- Zones werden bereits in HA Integration verwaltet
- Core Add-on sollte Zone-Daten **konsumieren**, nicht redundant speichern
- Empfehlung: WebSocket Event Stream + REST API Bridge

**Nächste Schritte:**
1. Zone Bridge zur HA Integration implementieren
2. Brain Graph Zone Nodes erweitern
3. Habitus Miner Zone-Filter aktivieren

**Offene Frage:** Architektur-Entscheidung Zone-Daten-Sync benötigt Bestätigung.

