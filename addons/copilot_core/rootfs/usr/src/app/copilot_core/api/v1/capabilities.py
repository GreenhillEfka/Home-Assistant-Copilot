"""API v1 – Capabilities endpoint.

Provides Core Add-on capabilities and status information for HA Integration
to determine what features are supported and whether Core is healthy.

Endpoints:
    GET /api/v1/capabilities    – Core capabilities and status
"""
from __future__ import annotations

import logging
from flask import Blueprint, jsonify

from copilot_core.api.security import require_token

logger = logging.getLogger(__name__)

bp = Blueprint("capabilities", __name__)


@bp.route("/api/v1/capabilities", methods=["GET"])
def get_capabilities():
    """Return Core Add-on capabilities and status.
    
    This endpoint allows the HA Integration to:
    1. Verify Core is reachable and healthy
    2. Determine which API endpoints are supported
    3. Check Core version compatibility
    4. Get configuration hints for optimal integration
    
    No authentication required for capabilities discovery.
    """
    
    # Core system info
    capabilities = {
        "core_version": "0.4.8",
        "api_version": "1.0",
        "status": "healthy",
        "ready": True,
        
        # API endpoints supported
        "endpoints": {
            "events_ingest": {
                "path": "/api/v1/events",
                "methods": ["POST", "GET"],
                "description": "Event ingestion and query",
                "batch_limit": 500,
                "requires_auth": True
            },
            "candidates": {
                "path": "/api/v1/candidates",
                "methods": ["GET", "POST"],
                "description": "Automation candidate management",
                "requires_auth": True
            },
            "brain_graph": {
                "path": "/api/v1/brain-graph",
                "methods": ["GET"],
                "description": "Activity graph visualization",
                "requires_auth": True
            },
            "capabilities": {
                "path": "/api/v1/capabilities",
                "methods": ["GET"],
                "description": "This endpoint",
                "requires_auth": False
            }
        },
        
        # Feature flags
        "features": {
            "event_envelope_v1": True,
            "privacy_redaction": True,
            "zone_enrichment": True,
            "candidate_lifecycle": True,
            "brain_graph": True,
            "habitus_mining": True,
            "mood_ranking": False,  # Not yet implemented
            "energy_analysis": False,  # Future feature
            "unifi_integration": False  # Future feature
        },
        
        # Integration hints for HA
        "integration_hints": {
            "recommended_batch_size": 50,
            "max_events_per_second": 100,
            "supported_event_kinds": [
                "state_changed",
                "call_service", 
                "automation_triggered",
                "script_started"
            ],
            "supported_domains": [
                "light", "switch", "sensor", "binary_sensor",
                "media_player", "climate", "cover", "lock",
                "alarm_control_panel", "camera", "vacuum"
            ],
            "privacy_domains": [
                "person", "device_tracker", "mobile_app"
            ]
        },
        
        # Health indicators
        "health": {
            "uptime_seconds": _get_uptime_seconds(),
            "last_event_ts": _get_last_event_timestamp(),
            "total_events_processed": _get_total_events(),
            "active_candidates": _get_active_candidates_count(),
            "storage_status": "ok"
        }
    }
    
    return jsonify(capabilities), 200


def _get_uptime_seconds() -> int:
    """Get Core Add-on uptime in seconds."""
    try:
        # Simple approach: read from /proc/uptime 
        with open('/proc/uptime', 'r') as f:
            uptime = float(f.read().split()[0])
            return int(uptime)
    except Exception as e:
        logger.debug(f"Unable to read uptime: {e}")
        return 0


def _get_last_event_timestamp() -> float | None:
    """Get timestamp of last processed event."""
    try:
        from copilot_core.api.v1.events_ingest import get_store
        store = get_store()
        stats = store.stats()
        return stats.get("last_event_ts")
    except Exception as e:
        logger.debug(f"Unable to get last event timestamp: {e}")
        return None


def _get_total_events() -> int:
    """Get total number of events processed."""
    try:
        from copilot_core.api.v1.events_ingest import get_store
        store = get_store()
        stats = store.stats()
        return stats.get("total_events", 0)
    except Exception as e:
        logger.debug(f"Unable to get total events: {e}")
        return 0


def _get_active_candidates_count() -> int:
    """Get count of active (pending) candidates."""
    try:
        from copilot_core.api.v1.candidates import candidate_service
        if candidate_service:
            stats = candidate_service.get_stats()
            return getattr(stats, 'pending_count', 0)
        return 0
    except Exception as e:
        logger.debug(f"Unable to get candidate count: {e}")
        return 0