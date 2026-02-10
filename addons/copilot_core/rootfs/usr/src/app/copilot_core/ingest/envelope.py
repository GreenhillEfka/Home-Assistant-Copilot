"""
Event envelope normalization and validation.

Implements the stable event schema from Alpha Worker n3_forwarder_quality specification.
Handles attribute projection, redaction policy, and zone enrichment.
"""

import re
import hashlib
from typing import Dict, Any, Optional, Set, List
from datetime import datetime, timezone


# Privacy patterns to redact
PII_PATTERNS = [
    re.compile(r'\b[\w._%+-]+@[\w.-]+\.[A-Z|a-z]{2,}\b'),  # emails
    re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),            # IP addresses
    re.compile(r'\b\d{3}-?\d{3}-?\d{4}\b'),                # phone numbers
    re.compile(r'\bhttps?://[^\s]+'),                       # URLs
    re.compile(r'(?:latitude|longitude|gps_accuracy)', re.I), # GPS coords
    re.compile(r'(?:token|key|secret|password)', re.I),    # Auth tokens
]

# Domain-specific attribute projection rules
DOMAIN_ATTRIBUTES = {
    "light": {"brightness", "color_temp", "rgb_color", "color_mode"},
    "climate": {"temperature", "current_temperature", "hvac_action", "humidity"},
    "media_player": {"media_content_type", "media_title", "media_artist", "source", "volume_level"},
    "binary_sensor": {"device_class"},
    "sensor": {"unit_of_measurement", "device_class", "state_class"},
    "cover": {"current_position", "current_tilt_position"},
    "lock": {"device_class"},
    "person": {"source_type"},  # GPS coords are redacted
    "device_tracker": {"source_type"},
    "weather": {"temperature", "humidity", "pressure", "wind_speed", "condition"},
    # Default: switch, input_boolean get no attributes (state-only)
}

# Always redact these attribute names
REDACTED_ATTRIBUTES = {
    "entity_picture", "media_image_url", "media_image_remotely_accessible",
    "latitude", "longitude", "gps_accuracy", "access_token", "token",
    "friendly_name"  # Can contain real names
}


class EventEnvelope:
    """Event envelope processor implementing Alpha Worker n3 specification."""
    
    SCHEMA_VERSION = 1
    
    def __init__(self, zone_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize envelope processor.
        
        Args:
            zone_mapping: Dict mapping entity_id -> zone_id for enrichment
        """
        self.zone_mapping = zone_mapping or {}
    
    def normalize_event(self, raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert raw HA event to normalized envelope.
        
        Args:
            raw_event: Raw event from HA WebSocket or HTTP API
            
        Returns:
            Normalized envelope dict or None if invalid/filtered
        """
        try:
            # Extract basic event info
            event_type = raw_event.get("event_type", "")
            event_data = raw_event.get("data", {})
            
            if event_type == "state_changed":
                return self._normalize_state_changed(event_data)
            elif event_type == "call_service":
                return self._normalize_service_call(event_data)
            
            # Other event types not supported yet
            return None
            
        except Exception as e:
            # Log error but don't crash pipeline
            return None
    
    def _normalize_state_changed(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize state_changed event."""
        entity_id = data.get("entity_id", "")
        if not entity_id:
            return None
        
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        new_state = data.get("new_state", {})
        old_state = data.get("old_state", {})
        
        # Extract and validate timestamps
        last_changed = new_state.get("last_changed")
        last_updated = new_state.get("last_updated")
        
        envelope = {
            "v": self.SCHEMA_VERSION,
            "ts": datetime.now(timezone.utc).isoformat(),
            "src": "ha",
            "kind": "state_changed",
            
            # Entity identification
            "entity_id": entity_id,
            "domain": domain,
            "zone_id": self._get_zone_for_entity(entity_id),
            
            # State delta with projected attributes
            "old": self._project_state(old_state, domain),
            "new": self._project_state(new_state, domain),
            
            # Timing
            "last_changed": last_changed,
            "last_updated": last_updated,
            
            # Causality (redacted)
            "context_id": self._redact_context_id(new_state.get("context", {}).get("id")),
            "parent_id": self._redact_context_id(new_state.get("context", {}).get("parent_id")),
            "trigger": self._infer_trigger(new_state.get("context", {})),
        }
        
        return envelope
    
    def _normalize_service_call(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize call_service event."""
        domain = data.get("domain", "")
        service = data.get("service", "")
        service_data = data.get("service_data", {})
        
        if not domain or not service:
            return None
        
        # Extract entity_id(s) from service_data
        entity_ids = service_data.get("entity_id", [])
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]
        
        envelope = {
            "v": self.SCHEMA_VERSION,
            "ts": datetime.now(timezone.utc).isoformat(),
            "src": "ha",
            "kind": "call_service",
            
            "domain": domain,
            "service": service,
            "entity_ids": entity_ids,
            "service_data": self._redact_service_data(service_data),
        }
        
        return envelope
    
    def _project_state(self, state_obj: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Project state object to minimal attributes per domain."""
        if not state_obj:
            return {"state": None, "attrs": {}}
        
        state_value = state_obj.get("state")
        attributes = state_obj.get("attributes", {})
        
        # Get allowed attributes for this domain
        allowed_attrs = DOMAIN_ATTRIBUTES.get(domain, set())
        
        # Project only allowed attributes, redact sensitive ones
        projected_attrs = {}
        for key, value in attributes.items():
            if key in REDACTED_ATTRIBUTES:
                continue
            if key in allowed_attrs:
                projected_attrs[key] = self._redact_value(value)
        
        return {
            "state": state_value,
            "attrs": projected_attrs
        }
    
    def _redact_value(self, value: Any) -> Any:
        """Redact PII from a value."""
        if isinstance(value, str):
            for pattern in PII_PATTERNS:
                value = pattern.sub("[REDACTED]", value)
        return value
    
    def _redact_service_data(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data from service call data."""
        redacted = {}
        for key, value in service_data.items():
            if key in REDACTED_ATTRIBUTES:
                redacted[key] = "[REDACTED]"
            elif any(pattern.search(key) for pattern in PII_PATTERNS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = self._redact_value(value)
        return redacted
    
    def _redact_context_id(self, context_id: Optional[str]) -> Optional[str]:
        """Truncate context ID to first 12 chars for privacy."""
        if not context_id:
            return None
        return context_id[:12]
    
    def _infer_trigger(self, context: Dict[str, Any]) -> str:
        """Infer trigger type from context."""
        if context.get("user_id"):
            return "user"
        elif context.get("parent_id"):
            return "automation"
        else:
            return "unknown"
    
    def _get_zone_for_entity(self, entity_id: str) -> Optional[str]:
        """Get zone mapping for entity (if configured)."""
        return self.zone_mapping.get(entity_id)
    
    def update_zone_mapping(self, mapping: Dict[str, str]):
        """Update the entity -> zone mapping."""
        self.zone_mapping.update(mapping)


# Global envelope processor instance
_envelope_processor: Optional[EventEnvelope] = None

def get_envelope_processor() -> EventEnvelope:
    """Get global envelope processor instance."""
    global _envelope_processor
    if _envelope_processor is None:
        _envelope_processor = EventEnvelope()
    return _envelope_processor

def init_envelope_processor(zone_mapping: Optional[Dict[str, str]] = None):
    """Initialize global envelope processor with zone mapping."""
    global _envelope_processor
    _envelope_processor = EventEnvelope(zone_mapping)