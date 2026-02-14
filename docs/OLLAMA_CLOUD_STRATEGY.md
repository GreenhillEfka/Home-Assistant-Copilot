# Ollama Cloud Model Strategy

## Policy: OLLAMA CLOUD FIRST 🚀

Wir nutzen primär **Ollama Cloud Modelle** für alle Entwicklungsaufgaben!

## Verfügbare Modelle

| Modell | Stärken | Einsatzzweck |
|--------|----------|--------------|
| `glm-5:cloud` | Bester Code, schnelle Antworten | Python/HA Code, Documentation, Routine-Tasks |
| `deepseek-r1:latest` | Bestes Reasoning, komplexe Analyse | Code Review, Architektur-Entscheidungen, Debugging |

## Modell-Auswahl-Matrix

| Task-Typ | Bevorzugtes Modell | Fallback |
|----------|-------------------|----------|
| Python/HA Code | `glm-5:cloud` | `deepseek-r1:latest` |
| Komplexe Analyse | `deepseek-r1:latest` | `glm-5:cloud` |
| Code Review | `deepseek-r1:latest` | `glm-5:cloud` |
| Documentation | `glm-5:cloud` | - |
| Routine-Tasks | `glm-5:cloud` | - |

## Worker-Konfiguration

Alle Worker sind auf Ollama Cloud konfiguriert:

| Worker | Modell | Intervall |
|--------|--------|-----------|
| Iteration Manager | `glm-5:cloud` | 5 min |
| Module Kernel Orchestrator | `glm-5:cloud` | 15 min |
| Autopilot | `glm-5:cloud` | 10 min |
| Decision Matrix | `glm-5:cloud` | 10 min |
| Telegram Progress | `glm-5:cloud` | 10 min |
| Debug Level Worker | `glm-5:cloud` | 30 min |
| PilotSuite Checkpoints | `glm-5:cloud` | 30 min |
| Dashboard UX Worker | `glm-5:cloud` | 30 min |
| Task Scout | `glm-5:cloud` | 15 min |

## Vorteile

1. **Kostenlos** - 12 Stunden Anfragen verfügbar
2. **Schnell** - glm-5:cloud ist sehr schnell
3. **Hohe Qualität** - Beide Modelle sind exzellent für Code
4. **Konsistent** - Einheitliche Modell-Nutzung

## Konfiguration

```bash
# Primary Model
export OLLAMA_HOST="http://192.168.31.84:11434"

# Model Priority
glm-5:cloud > deepseek-r1:latest > codellama:latest
```

## Monitoring

Worker-Logs zeigen:
- Modell-Nutzung
- Token-Verbrauch
- Laufzeiten

*Letzte Aktualisierung: 2026-02-14*
