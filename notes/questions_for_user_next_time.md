# Fragen / Klärungen (beim nächsten Online-Sein)

(Autopilot sammelt hier Rückfragen; nichts davon ist dringend.)

- Wollen wir AICoPilot-Tags **immer** als HA-Labels materialisieren (Default: ja), oder nur für ausgewählte Facetten (z. B. `role.*`, `state.*`)?
- Welche **Subjects** sollen v0.1 unterstützen: nur `entity` + `device` + `area`, oder auch `automation/scene/script/helper` (HA kann Labels dafür im UI)?
- Sollen wir als interne Referenz für Subjects primär `entity_id` verwenden oder lieber Registry-IDs/`unique_id`/`device_id` (stabiler bei Rename)?
- Namespace-Policy: Ist `user.*` gewünscht (Nutzer definieren eigene Tags), oder sollen Nutzer nur über HA-Labels arbeiten und AICoPilot importiert sie optional?
- Lokalisierung: Reicht `display.de` (und später `en`), oder sollen wir von Anfang an i18n-konform arbeiten?
- Learned/Candidate Tags: Dürfen die jemals automatisch als HA-Label erscheinen, oder nur nach expliziter Bestätigung (empfohlen: nur nach Bestätigung)?
- Farben/Icons: Wollen wir (a) zentral im Tag-Registry-Objekt pflegen und nach HA syncen, oder (b) HA als UI-Quelle akzeptieren und nur IDs synchron halten?
- Konflikte/Duplikate: Wie sollen wir umgehen, wenn ein Nutzer schon ein HA-Label „Sicherheitskritisch“ hat, aber ohne `aicp.*` Namespace?
- Habitus-Zonen: Sollen diese als eigene interne Objekte mit Policies modelliert werden (wie im Doc), oder reicht reines Tagging ohne extra Objekt?
- Migration: Gibt es bereits Legacy-Listen/Configs, die wir einsammeln müssen (wo liegen sie), oder starten wir bei 0?
