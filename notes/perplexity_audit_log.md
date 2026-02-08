# Perplexity Deep Audit — Quercheck Log

Ziel: stündlicher Quercheck des AI Home CoPilot Systems. Pro Run mindestens:
- 1 Verbesserungsvorschlag
- 1 Erweiterungsvorschlag

---

## Run: 2026-02-08 06:27 (Europe/Berlin)

**Prompt (Deep-Audit):**
Tag-System für AI Home CoPilot (Taxonomie/Namensschema, Semantik, HA-Mapping, Nutzung in Habitus/Inventory/Candidates/Repairs/Brain-Graph, Governance/Privacy, Migration, Datenmodelle+YAML, Integration vs Core; deutsches Markdown).

**Raw result (Perplexity JSON):**
```json
{
  "model": "sonar-pro",
  "answer": "# Deep-Audit: Tag-System für AI Home CoPilot\n\n## Executive Summary\n\nDie Suchergebnisse bieten Einblicke in Home Assistants **natives Tag-System** (NFC/RFID) und **AI-Integration**, adressieren aber nicht direkt ein umfassendes Governance-Framework für ein semantisches Tag-System mit Taxonomie, Versionierung und Brain-Graph-Integration. Basierend auf den verfügbaren Informationen und Best Practices skizziere ich ein implementierbares Konzept mit klaren Entscheidungen und offenen Fragen.\n\n---\n\n## 1. Semantische Differenzierung: Tag vs. Rolle vs. Label vs. Kategorie\n\n### Definitionen (Home Assistant Kontext)\n\n| Konzept | Definition | Home Assistant Mapping | Scope |\n|---------|-----------|----------------------|-------|\n| **Tag** | Scanbare Identifier (NFC/RFID) für Event-Trigger[1] | `tag_scanned` Event + Tag Entity | Device/Raum-spezifisch |\n| **Label** | Organisatorische Kategorisierung von Automationen/Skripten | `labels` in Automation/Script | Logisch, Cross-Domain |\n| **Area** | Physische/logische Raumzuordnung[1] | Device/Entity Registry Area | Hierarchisch |\n| **Rolle** | Funktionale Verantwortung (z.B. \"Bewegungsmelder\", \"Heizregler\") | Custom Attribute + Device Class | Semantisch |\n| **Kategorie** | Taxonomische Klassifikation (z.B. \"Sicherheit\", \"Komfort\") | Label-Hierarchie | Governance-Level |\n\n**Entscheidung:** Tags bleiben **Event-Trigger-Mechanismus**; semantische Struktur wird durch **Labels + Custom Attributes** realisiert.\n\n---\n\n## 2. Taxonomie & Namensschema\n\n### Namespace-Struktur\n\n```yaml\n# Format: {domain}:{category}:{subcategory}:{entity_type}:{version}\n# Beispiele:\n\ntags:\n  nfc_music_bedroom_v1:\n    namespace: \"home.automation.media\"\n    scope: \"bedroom\"\n    version: \"1.0\"\n    language: \"de\"\n    \nlabels:\n  # Kategorien (Governance-Level)\n  cat_security:\n    de: \"Sicher",
  "citations": [
    "https://www.home-assistant.io/integrations/tag/",
    "https://www.home-assistant.io/blog/2020/09/15/home-assistant-tags/",
    "https://www.home-assistant.io/blog/2025/09/11/ai-in-home-assistant/",
    "https://www.strikegraph.com/blog/ai-internal-compliance-audit",
    "https://www.tag1.com/blog/how-ai-helped-make-home-assistant-contribution/",
    "https://github.com/Coolver/home-assistant-vibecode-agent",
    "https://hoop.dev/blog/how-to-keep-ai-audit-trail-ai-operations-automation-secure-and-compliant-with-access-guardrails/",
    "https://www.youtube.com/watch?v=vMdpLiAB9dI"
  ]
}
```

**Notes:** Antwort wurde wegen Token-Limit abgeschnitten; ggf. erneut mit Fokus (z.B. nur Datenmodell+YAML) nachziehen.
