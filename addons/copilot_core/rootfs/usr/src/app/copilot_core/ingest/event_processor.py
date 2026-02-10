"""
Event processing pipeline connecting EventStore to BrainGraphService.

This module provides automatic processing of ingested events to update 
the brain graph with real-time smart home state and relationships.
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from ..brain_graph.service import BrainGraphService
from ..dev_surface.service import dev_surface
from .envelope import get_envelope_processor

logger = logging.getLogger(__name__)


class EventProcessor:
    """
    Processes events from EventStore and forwards them to downstream services.
    
    Currently supports:
    - BrainGraphService integration for knowledge graph updates
    - Configurable event filters and processors
    """
    
    def __init__(self, brain_graph_service: Optional[BrainGraphService] = None):
        self.brain_graph_service = brain_graph_service
        self.processors: List[Callable[[Dict[str, Any]], None]] = []
        
        # Register default processors
        if brain_graph_service:
            self.processors.append(self._process_for_brain_graph)
    
    def add_processor(self, processor: Callable[[Dict[str, Any]], None]):
        """Add a custom event processor function."""
        self.processors.append(processor)
    
    def process_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of events through all registered processors.
        
        Args:
            events: List of raw event dictionaries from EventStore
            
        Returns:
            Processing statistics
        """
        envelope_processor = get_envelope_processor()
        
        stats = {
            "processed": 0,
            "errors": 0,
            "brain_graph_updates": 0,
            "normalized": 0,
            "filtered": 0
        }
        
        for event in events:
            try:
                # Normalize event through envelope processor
                normalized_event = envelope_processor.normalize_event(event)
                
                if normalized_event is None:
                    stats["filtered"] += 1
                    continue
                
                stats["normalized"] += 1
                
                # Process normalized event through all processors
                for processor in self.processors:
                    processor(normalized_event)
                    
                stats["processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing event {event.get('id', 'unknown')}: {e}")
                dev_surface.error("event_processor", f"Failed to process event {event.get('id', 'unknown')}", error=e, context={"event": event})
                stats["errors"] += 1
        
        # Track processed events for metrics
        dev_surface.increment_events_processed(stats["processed"])
        
        if stats["processed"] > 0:
            dev_surface.debug("event_processor", f"Processed {stats['processed']} events successfully (normalized: {stats['normalized']}, filtered: {stats['filtered']})")
        
        return stats
    
    def _process_for_brain_graph(self, event: Dict[str, Any]):
        """Process event for brain graph updates."""
        if not self.brain_graph_service:
            return
        
        try:
            kind = event.get("kind", "")
            
            if kind == "state_changed":
                self._process_state_change_for_graph(event)
            elif kind == "call_service":  
                self._process_service_call_for_graph(event)
            
        except Exception as e:
            logger.error(f"Brain graph processing error for event {event.get('id')}: {e}")
    
    def _process_state_change_for_graph(self, event: Dict[str, Any]):
        """Process normalized state_changed events for brain graph."""
        entity_id = event.get("entity_id", "")
        domain = event.get("domain", "")
        zone_id = event.get("zone_id")
        
        if not entity_id or not domain:
            return
            
        # Create/touch entity node
        entity_label = entity_id.split(".")[-1].replace("_", " ").title()
        
        node_meta = {
            "envelope_version": event.get("v", 1),
            "trigger": event.get("trigger", "unknown")
        }
        
        if zone_id:
            node_meta["zone_id"] = zone_id
            
        # Get new state info from normalized envelope
        new_state = event.get("new", {})
        if new_state:
            state_value = new_state.get("state")
            if state_value:
                node_meta["last_state"] = state_value
            
            # Store projected attributes (already filtered/redacted)
            attrs = new_state.get("attrs", {})
            if attrs:
                node_meta.update(attrs)
        
        entity_node = self.brain_graph_service.touch_node(
            node_id=f"ha.entity:{entity_id}",
            delta=0.5,  # Moderate score boost for state changes
            label=entity_label,
            kind="entity",
            domain=domain,
            meta_patch=node_meta,
            source={"system": "ha", "event": "state_changed"},
            tags=[f"domain:{domain}", f"trigger:{event.get('trigger', 'unknown')}"]
        )
        
        # Create zone node and link if zone_id exists
        if zone_id:
            zone_node = self.brain_graph_service.touch_node(
                node_id=f"ha.zone:{zone_id}",
                delta=0.1,  # Small boost for zones
                label=zone_id.replace("_", " ").title(),
                kind="zone", 
                domain="zone",
                source={"system": "ha", "event": "state_changed"}
            )
            
            # Link entity to zone
            self.brain_graph_service.link(
                from_node=entity_node.id,
                to_node=zone_node.id,
                edge_type="in_zone",
                initial_weight=0.3
            )
    
    def _process_service_call_for_graph(self, event: Dict[str, Any]):
        """Process normalized call_service events for brain graph."""
        domain = event.get("domain", "")
        service = event.get("service", "")
        entity_ids = event.get("entity_ids", [])
        
        if not domain or not service:
            return
            
        # Create/touch service node
        service_node_id = f"ha.service:{domain}.{service}"
        service_node = self.brain_graph_service.touch_node(
            node_id=service_node_id,
            delta=0.8,  # Higher score for service calls (intentional actions)
            label=f"{service.replace('_', ' ').title()}",
            kind="service",
            domain=domain,
            source={"system": "ha", "event": "call_service"},
            tags=[f"domain:{domain}", f"service:{service}"]
        )
        
        # Link to target entity if specified
        if entity_id:
            entity_domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
            entity_label = entity_id.split(".")[-1].replace("_", " ").title() if "." in entity_id else entity_id
            entity_node = self.brain_graph_service.touch_node(
                node_id=f"ha.entity:{entity_id}",
                delta=0.3,  # Boost for being target of service call
                label=entity_label,
                kind="entity",
                domain=entity_domain,
                source={"system": "ha", "event": "call_service"}
            )
            
            # Link service to entity
            self.brain_graph_service.link(
                from_node=service_node.id,
                to_node=entity_node.id,
                edge_type="targets",
                initial_weight=0.6
            )


# Global processor instance - initialized by main.py
_processor: Optional[EventProcessor] = None


def get_processor() -> Optional[EventProcessor]:
    """Get the global event processor instance."""
    return _processor


def set_processor(processor: EventProcessor):
    """Set the global event processor instance."""
    global _processor
    _processor = processor