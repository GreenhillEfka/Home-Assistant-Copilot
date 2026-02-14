# AI Home CoPilot - API Reference

## Core Add-on REST API v1

**Base URL**: `http://127.0.0.1:8686/api/v1/`

Alle Endpoints unterstützen JSON-Format. Optional: Auth Token über `Authorization: Bearer <token>` Header.

## Authentication (Optional)

```yaml
# Core Add-on Config
auth:
  enabled: true
  tokens:
    - "your-secret-token"
```

```bash
# API Request mit Auth
curl -H "Authorization: Bearer your-secret-token" \
     http://127.0.0.1:8686/api/v1/capabilities
```

---

## Endpoints

### GET `/api/v1/capabilities`

**Zweck**: System-Fähigkeiten und Health-Status abrufen

**Auth**: Nicht erforderlich (Public Discovery)

**Response**:
```json
{
  "name": "AI Home CoPilot Core",
  "version": "0.4.9",
  "api": {
    "version": "v1",
    "endpoints": ["/events", "/candidates", "/brain", "/dashboard"]
  },
  "features": {
    "event_ingestion": true,
    "candidate_generation": true,
    "brain_graph": true,
    "dashboard": true,
    "auth_required": false
  },
  "health": {
    "status": "healthy",
    "uptime_seconds": 145823,
    "events_processed": 45231,
    "candidates_active": 12
  },
  "integration_hints": {
    "recommended_poll_interval": 300,
    "batch_size_limit": 100,
    "auth_setup_required": false
  }
}
```

**Use Cases**:
- HA Integration compatibility check
- Service discovery
- Health monitoring

---

### POST `/api/v1/events`

**Zweck**: Home Assistant Events einreichen

**Auth**: Optional (basierend auf Core Config)

**Request Body**:
```json
{
  "events": [
    {
      "entity_id": "light.living_room",
      "state": "on",
      "timestamp": "2026-02-10T13:45:30Z",
      "domain": "light",
      "zone": "living_room",
      "attributes": {
        "brightness": 180,
        "color_temp": 370
      }
    }
  ]
}
```

**Response**:
```json
{
  "processed": 1,
  "errors": [],
  "envelope_version": 1
}
```

**Event Envelope Schema**:
- **entity_id** (string): HA Entity ID
- **state** (string): Neuer Zustand  
- **timestamp** (ISO 8601): Event-Zeitpunkt
- **domain** (string): HA Domain (light, sensor, etc.)
- **zone** (string): Bereich/Raum
- **attributes** (object): Domain-spezifische Attribute

**Privacy-Features**:
- PII-Redaction in entity names
- GPS-Koordinaten gefiltert  
- Context-ID gekürzt
- Attribute-Projection pro Domain

---

### GET `/api/v1/candidates`

**Zweck**: Aktuelle Automatisierungs-Kandidaten abrufen

**Auth**: Empfohlen

**Query Parameters**:
- `status` (string): `active`, `deferred`, `evidence` 
- `limit` (int): Max. Anzahl (default: 50)
- `zone` (string): Filter nach Bereich

**Response**:
```json
{
  "candidates": [
    {
      "id": "cand_001",
      "type": "pattern_automation",
      "title": "Küche Abends-Routine",
      "description": "Licht + Kaffeemaschine werden oft zusammen geschaltet (18:00-20:00)",
      "confidence": 0.85,
      "status": "active",
      "entities": ["light.kitchen", "switch.coffee_maker"],
      "zone": "kitchen", 
      "created_at": "2026-02-09T20:15:00Z",
      "evidence": {
        "pattern_frequency": 23,
        "time_window": "18:00-20:00",
        "last_occurred": "2026-02-10T19:45:00Z"
      },
      "suggested_automation": {
        "trigger": "time_based",
        "conditions": ["sun.sun below_horizon"],
        "actions": ["turn_on: light.kitchen", "turn_on: switch.coffee_maker"]
      }
    }
  ],
  "total": 12,
  "summary": {
    "active": 8,
    "deferred": 3,  
    "evidence": 1
  }
}
```

---

### POST `/api/v1/candidates/{id}/defer`

**Zweck**: Kandidat temporär zurückstellen

**Auth**: Empfohlen

**Request Body**:
```json
{
  "reason": "user_feedback",
  "defer_until": "2026-02-17T10:00:00Z"
}
```

**Response**:
```json
{
  "success": true,
  "candidate_id": "cand_001",
  "status": "deferred",
  "defer_until": "2026-02-17T10:00:00Z"
}
```

---

### GET `/api/v1/brain/graph`

**Zweck**: Brain Graph Visualisierung abrufen

**Auth**: Optional

**Query Parameters**:
- `format` (string): `json`, `svg` (default: json)
- `limit` (int): Max. Knoten (20-80, default: 50)
- `zone` (string): Filter nach Bereich
- `dashboard` (bool): Optimiert für Dashboard (default: false)

**Response (JSON)**:
```json
{
  "nodes": [
    {
      "id": "light.living_room", 
      "domain": "light",
      "zone": "living_room",
      "activity_score": 0.78,
      "connections": 3,
      "last_seen": "2026-02-10T13:40:00Z"
    }
  ],
  "edges": [
    {
      "source": "light.living_room",
      "target": "media_player.tv",
      "weight": 0.65,
      "correlation": "temporal",
      "frequency": 45
    }
  ],
  "metadata": {
    "total_nodes": 87,
    "rendered_nodes": 50,
    "time_window": "24h",
    "last_updated": "2026-02-10T13:45:00Z"
  }
}
```

**Response (SVG)**:
```xml
<svg width="800" height="600" xmlns="...">
  <!-- Optimierte Darstellung für Dashboards -->
  <circle cx="100" cy="100" r="20" fill="#4CAF50"/>
  <text x="100" y="105">Living Room</text>
  <!-- ... weitere Graph-Elemente -->
</svg>
```

---

### GET `/api/v1/dashboard`

**Zweck**: Dashboard-Summary für HA Frontend

**Auth**: Optional

**Response**:
```json
{
  "health": {
    "score": 78,
    "status": "good", 
    "last_updated": "2026-02-10T13:45:00Z"
  },
  "activity": {
    "events_24h": 1247,
    "entities_active": 45,
    "top_entities": [
      {
        "entity_id": "sensor.temperature_living_room",
        "domain": "sensor", 
        "activity_count": 156,
        "zone": "living_room"
      }
    ]
  },
  "candidates": {
    "active": 8,
    "new_since_yesterday": 2,
    "top_candidate": {
      "title": "Küche Abends-Routine",
      "confidence": 0.85
    }
  },
  "brain_graph": {
    "total_nodes": 87,
    "total_connections": 234,  
    "most_connected": {
      "entity_id": "light.living_room",
      "connections": 12
    }
  },
  "recommendations": [
    "Erwäge Allowlist-Erweiterung: 15 neue Entities erkannt",
    "Aktivitäts-Peak um 19:00 - perfekt für Timer-Automationen",
    "Starke Korrelationen in 'Kitchen' Zone - Automatisierungs-Potenzial"
  ],
  "system": {
    "uptime_hours": 40.5,
    "memory_usage_mb": 128,
    "events_processed": 45231
  }
}
```

**Health Score Algorithm**:
```
Score = (Activity_Weight * 40) + (Connectivity_Weight * 35) + (Stability_Weight * 25)

Activity_Weight: Events/hour, entity diversity
Connectivity_Weight: Edge density, correlation strength  
Stability_Weight: Error rate, service uptime
```

---

## HA Integration API (Internal)

### Button Entity: `button.copilot_brain_dashboard_summary`

**Zweck**: Dashboard-Summary in HA Frontend anzeigen

**Behavior**:
1. User drückt Button
2. Integration ruft `/api/v1/dashboard` auf
3. Zeigt Health Score + Recommendations als Notification

**Attribute**:
```yaml
friendly_name: "CoPilot Brain Dashboard Summary"
icon: mdi:brain
device_class: restart
```

---

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Entity ID format invalid",
    "details": {
      "field": "entity_id",
      "expected": "domain.name",
      "received": "invalid_format"
    }
  },
  "request_id": "req_12345",
  "timestamp": "2026-02-10T13:45:30Z"
}
```

### Error Codes
- **AUTH_REQUIRED** (401): Token fehlt/ungültig
- **INVALID_REQUEST** (400): Request-Format fehlerhaft
- **RATE_LIMITED** (429): Zu viele Requests
- **SERVICE_UNAVAILABLE** (503): Core Add-on offline
- **INTERNAL_ERROR** (500): Unerwarteter Fehler

---

## Rate Limiting

### Default Limits
- **Events**: 100 events/second, 10.000/hour
- **Candidates**: 60 requests/minute
- **Brain Graph**: 10 requests/minute (SVG), 60/minute (JSON)
- **Dashboard**: 30 requests/minute

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1644512400
```

---

## Examples

### Full Integration Setup
```python
# HA Integration → Core API
import aiohttp

class CoPilotAPI:
    def __init__(self, base_url="http://127.0.0.1:8686/api/v1", token=None):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    async def check_capabilities(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/capabilities") as response:
                return await response.json()
    
    async def submit_events(self, events):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/events",
                json={"events": events},
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def get_dashboard(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/dashboard", 
                headers=self.headers
            ) as response:
                return await response.json()

# Usage
api = CoPilotAPI(token="your-token")
capabilities = await api.check_capabilities()
dashboard = await api.get_dashboard()
print(f"Health Score: {dashboard['health']['score']}")
```

### Event Submission Example
```bash
# Bulk Event Submission
curl -X POST http://127.0.0.1:8686/api/v1/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "events": [
      {
        "entity_id": "light.bedroom",
        "state": "off", 
        "timestamp": "2026-02-10T22:30:00Z",
        "domain": "light",
        "zone": "bedroom",
        "attributes": {"brightness": 0}
      },
      {
        "entity_id": "sensor.bedroom_temperature", 
        "state": "19.5",
        "timestamp": "2026-02-10T22:30:00Z",
        "domain": "sensor", 
        "zone": "bedroom",
        "attributes": {"unit_of_measurement": "°C"}
      }
    ]
  }'
```

---

## Migration & Versioning

### API Versioning
- **Current**: v1 (stable)
- **Backward Compatibility**: 2 minor versions
- **Breaking Changes**: Neue Major Version (v2)

### Upgrade Path
```yaml
# Feature Detection
capabilities = GET /api/v1/capabilities
if "dashboard" in capabilities.features:
    # Use new Dashboard API
    dashboard = GET /api/v1/dashboard
else:
    # Fallback to legacy methods
    candidates = GET /api/v1/candidates
```

### Schema Evolution
- Neue Felder: **Optional, backward-compatible**
- Entfernte Felder: **Deprecated in v1.x, removed in v2.0**
- Changed Types: **Breaking change → Major version bump**

---

Ready for API Integration? 🚀

Die API ist vollständig dokumentiert und ready for production. Alle Endpoints sind getestet und unterstützen sowohl Entwicklung als auch productive Deployments.