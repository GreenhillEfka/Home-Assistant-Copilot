# MEMORY.md - Long-Term Memory

## Preferences / Operating Principles
- **Sicherheit zuerst.** Bei unklaren oder potenziell riskanten Aktionen lieber nachfragen und konservativ handeln.
- **Stetig professioneller werden.** Arbeitsweise iterativ verbessern (Playbooks/Checklisten), Fehler/Erkenntnisse dokumentieren.
- **Kontinuität:** Wichtige gemeinsam erarbeitete Setups/Entscheidungen dauerhaft festhalten (Konfig-Pfade, Geräte/Entity-IDs, Trigger/Workflows).

## Smart Home (Home Assistant)
- Aktionen, die etwas schalten/ändern: **erst bestätigen lassen** („Ja“), Read-only geht sofort.
- Bei Gruppen (z.B. Lichter): **immer Mitglieder/Segmente identifizieren und einzeln setzen**; Gruppen-State kann verzögert sein.

## Integrationen (Stand 2026-02)
- Telegram Bot: `@HomeClaw1_Bot` (DM-Pairing).
- Perplexity direkt (on-demand) via Workspace-Skripte:
  - Quick: `pplx:` → `sonar-pro`
  - Deep: `pplx-deep:` → `sonar-reasoning-pro`
  - Erzwinge Sprache: **Deutsch** (System-Prompt im Script).
