#!/usr/bin/env python3
"""
Test script for the new EventEnvelope implementation.
Validates Alpha Worker n3_forwarder_quality specification compliance.
"""

import json
from datetime import datetime, timezone
from copilot_core.ingest.envelope import EventEnvelope

def test_state_changed_event():
    """Test state_changed event normalization."""
    print("Testing state_changed event normalization...")
    
    # Sample raw HA state_changed event
    raw_event = {
        "event_type": "state_changed",
        "data": {
            "entity_id": "light.bed_light",
            "old_state": {
                "state": "off",
                "attributes": {
                    "brightness": None,
                    "color_temp": None,
                    "friendly_name": "Bedroom Light",  # Should be redacted
                    "supported_features": 47  # Should be filtered out for light domain
                },
                "context": {"id": "326ef27d1941abc123456789", "parent_id": None},
                "last_changed": "2026-02-08T23:18:00Z",
                "last_updated": "2026-02-08T23:18:00Z"
            },
            "new_state": {
                "state": "on",
                "attributes": {
                    "brightness": 180,  # Should be kept (light domain)
                    "color_temp": 380,  # Should be kept (light domain)
                    "friendly_name": "Bedroom Light",  # Should be redacted
                    "supported_features": 47,  # Should be filtered out
                    "entity_picture": "http://example.com/pic.jpg"  # Should be redacted
                },
                "context": {"id": "326ef27d1941abc123456789", "parent_id": None},
                "last_changed": "2026-02-08T23:19:00Z",
                "last_updated": "2026-02-08T23:19:00Z"
            }
        }
    }
    
    # Create envelope processor with sample zone mapping
    zone_mapping = {"light.bed_light": "bedroom"}
    envelope = EventEnvelope(zone_mapping)
    
    # Normalize the event
    normalized = envelope.normalize_event(raw_event)
    
    print("Normalized event:")
    print(json.dumps(normalized, indent=2))
    
    # Verify key properties
    assert normalized["v"] == 1, "Schema version should be 1"
    assert normalized["kind"] == "state_changed", "Event kind should be state_changed"
    assert normalized["entity_id"] == "light.bed_light", "Entity ID should be preserved"
    assert normalized["domain"] == "light", "Domain should be extracted"
    assert normalized["zone_id"] == "bedroom", "Zone should be enriched from mapping"
    assert normalized["context_id"] == "326ef27d1941", "Context ID should be truncated to 12 chars"
    
    # Verify attribute projection (only brightness and color_temp should remain)
    new_attrs = normalized["new"]["attrs"]
    assert "brightness" in new_attrs, "Brightness should be kept for light domain"
    assert "color_temp" in new_attrs, "Color temp should be kept for light domain" 
    assert "supported_features" not in new_attrs, "Supported features should be filtered out"
    assert "friendly_name" not in new_attrs, "Friendly name should be redacted"
    assert "entity_picture" not in new_attrs, "Entity picture should be redacted"
    
    print("✅ state_changed test passed!")

def test_service_call_event():
    """Test call_service event normalization."""
    print("\nTesting call_service event normalization...")
    
    raw_event = {
        "event_type": "call_service",
        "data": {
            "domain": "light",
            "service": "turn_on", 
            "service_data": {
                "entity_id": ["light.bed_light", "light.desk_light"],
                "brightness": 255,
                "password": "secret123"  # Should be redacted
            }
        }
    }
    
    envelope = EventEnvelope()
    normalized = envelope.normalize_event(raw_event)
    
    print("Normalized service call:")
    print(json.dumps(normalized, indent=2))
    
    assert normalized["kind"] == "call_service", "Event kind should be call_service"
    assert normalized["domain"] == "light", "Domain should be preserved"
    assert normalized["service"] == "turn_on", "Service should be preserved"
    assert len(normalized["entity_ids"]) == 2, "Entity IDs should be preserved"
    assert "brightness" in normalized["service_data"], "Non-sensitive data should be preserved"
    assert normalized["service_data"]["password"] == "[REDACTED]", "Password should be redacted"
    
    print("✅ call_service test passed!")

def test_pii_redaction():
    """Test PII redaction functionality."""
    print("\nTesting PII redaction...")
    
    envelope = EventEnvelope()
    
    test_cases = [
        ("user@example.com", "[REDACTED]"),
        ("192.168.1.100", "[REDACTED]"),
        ("555-123-4567", "[REDACTED]"),
        ("https://example.com/path", "[REDACTED]"),
        ("normal text", "normal text"),
    ]
    
    for input_val, expected in test_cases:
        result = envelope._redact_value(input_val)
        assert result == expected, f"Expected {expected}, got {result} for input {input_val}"
        print(f"  '{input_val}' → '{result}' ✅")

def test_domain_attribute_filtering():
    """Test domain-specific attribute filtering."""
    print("\nTesting domain-specific attribute filtering...")
    
    envelope = EventEnvelope()
    
    # Light domain should only keep brightness, color_temp, rgb_color, color_mode
    light_state = {
        "state": "on",
        "attributes": {
            "brightness": 200,      # Keep
            "color_temp": 380,      # Keep
            "rgb_color": [255, 0, 0], # Keep
            "supported_features": 47, # Filter out
            "effect_list": ["rainbow"], # Filter out
            "friendly_name": "Test Light" # Redact
        }
    }
    
    projected = envelope._project_state(light_state, "light")
    attrs = projected["attrs"]
    
    assert "brightness" in attrs, "Brightness should be kept"
    assert "color_temp" in attrs, "Color temp should be kept"
    assert "rgb_color" in attrs, "RGB color should be kept"
    assert "supported_features" not in attrs, "Supported features should be filtered"
    assert "effect_list" not in attrs, "Effect list should be filtered"
    assert "friendly_name" not in attrs, "Friendly name should be redacted"
    
    print("  Light domain filtering ✅")
    
    # Unknown domain should get no attributes
    unknown_state = {
        "state": "test",
        "attributes": {
            "some_attr": "value",
            "another_attr": 123
        }
    }
    
    projected = envelope._project_state(unknown_state, "unknown_domain")
    assert len(projected["attrs"]) == 0, "Unknown domains should get no attributes"
    
    print("  Unknown domain filtering ✅")

if __name__ == "__main__":
    print("🧪 Testing EventEnvelope implementation against Alpha Worker n3 spec\n")
    
    test_state_changed_event()
    test_service_call_event()
    test_pii_redaction()
    test_domain_attribute_filtering()
    
    print("\n🎉 All tests passed! EventEnvelope is compliant with Alpha Worker n3_forwarder_quality spec.")