# AI Home CoPilot - Entwicklungs-Index

## 🎯 Erstes Gesamtziel: v0.7.0 Release

**Prinzip:** HA Integration UND Core Add-on werden **synchron** entwickelt und released.

---

## 🔄 Zwei-Repo Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Home CoPilot                          │
├─────────────────────────────────────────────────────────────┤
│  HA Integration              │  Core Add-on              │
│  (ai_home_copilot_hacs_repo) │  (ha-copilot-repo)        │
│                              │                           │
│  • Entities                 │  • Neurons                │
│  • Services                 │  • Brain Graph            │
│  • Config Flow              │  • API Endpoints          │
│  • Dashboard UX             │  • Event Processing       │
└────────────────────────────┴────────────────────────────┘
           ↓                              ↓
        Beide repos werden synchron released!
```

---

## ✅ Completed Modules (v0.6.1)

### HA Integration + Core Add-on同步

| Feature | HA Integration | Core Add-on | Status |
|---------|---------------|-------------|--------|
| **Mood Module** | ✅ Ready | ✅ Mood Neuron | ✅ Done |
| **Media Context v2** | ✅ Ready | ✅ Media Neuron | ✅ Done |
| **Energy Module** | ✅ Ready | ✅ Energy Neuron | ✅ Done |
| **Debug Level v0.6** | ✅ Ready | - | ✅ Done |
| **Forwarder Quality** | ✅ Ready | ✅ Forwarder Neuron | ✅ Done |
| **Tag System** | ✅ Ready | ✅ Tag Neuron | ✅ Done |
| **Dev Surface** | ✅ Ready | - | ✅ Done |
| **Diagnostics Contract** | ✅ Ready | - | ✅ Done |
| **Log Fixer TX** | ✅ Ready | - | ✅ Done |
| **Inventory** | ✅ Ready | - | ✅ Done |

---

## 🔶 In Progress

| Feature | HA Integration | Core Add-on | Status |
|---------|---------------|-------------|--------|
| **UniFi Module** | ⚠️ needs_fixes | ✅ UniFi Neuron | 🔶 Testing |
| **Brain Graph v2** | 🔶 Testing | ✅ Brain Graph Neuron | ✅ Done |

---

## 📝 Todo / Backlog

| Feature | HA Integration | Core Add-on | Priority |
|---------|---------------|-------------|----------|
| **Habitus Zones v2** | Todo | - | High |
| **Habitus Dashboard Cards** | Todo | - | Medium |
| **Brain Graph Viz** | Todo | - | Medium |
| **Graph Candidates Bridge** | Todo | ✅ Candidate Neuron | Medium |
| **Candidates Store** | Todo | - | Medium |
| **Ops Runbook** | Todo | - | Low |
| **System Health** | Todo | ✅ Health Neuron | Low |
| **Update Rollback** | Todo | - | Low |
| **Performance Scaling** | Todo | - | Low |
| **Security Privacy** | Todo | - | Low |
| **Repairs Blueprints** | Todo | - | Low |

---

## 📊 Fortschritt

```
HA Integration:     10/22 Modules done (45%)
Core Add-on:        7/12 Neurons done (58%)

Sync Status:        7 Features fully synchronized
```

---

## 🔄 Synchronisations-Regeln

1. **Beide Repos werden im selben Release-Zyklus aktualisiert**
2. **Kein Feature gilt als "done" bis beide Seiten implementiert sind**
3. **Versionen werden parallel gebumpt** (z.B. Integration v0.6.1 + Add-on v0.4.1)
4. **Changelog listet beide Änderungen**

---

## 📁 Verknüpfte Dokumente

- HA Integration: `/config/.openclaw/workspace/ai_home_copilot_hacs_repo`
- Core Add-on: `/config/.openclaw/workspace/ha-copilot-repo`
- Specs: `docs/module_specs/`
- Reports: `notes/module_test_reports/`
- Worker: `docs/worker_templates/ITERATION_MANAGER.md`

---

*Letzte Aktualisierung: 2026-02-14*
