"""
Brain Graph Dashboard API - N4 enhancement.

Provides a consolidated view of brain graph metrics, recent activity, 
and system health for HA Integration display.
"""

from flask import Blueprint, request, jsonify, Response
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from ..security import require_api_key
from ...brain_graph.service import BrainGraphService
from ...brain_graph.render import GraphRenderer  
from ...ingest.event_store import EventStore
from ...candidates.service import CandidateService

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1/dashboard')

# Global service instances
_brain_graph_service: Optional[BrainGraphService] = None
_event_store: Optional[EventStore] = None
_candidate_service: Optional[CandidateService] = None

def init_dashboard_api(
    brain_graph: BrainGraphService,
    event_store: EventStore = None,
    candidate_service: CandidateService = None
):
    """Initialize dashboard API with service instances."""
    global _brain_graph_service, _event_store, _candidate_service
    _brain_graph_service = brain_graph
    _event_store = event_store
    _candidate_service = candidate_service

@dashboard_bp.route('/brain-summary', methods=['GET'])
@require_api_key
def get_brain_summary() -> Response:
    """
    Get consolidated brain graph summary for HA dashboard.
    
    Returns:
    - Brain graph node/edge counts and health
    - Recent activity metrics (24h)
    - Top entities by activity
    - Candidate detection summary
    - System uptime and status
    """
    if not _brain_graph_service:
        return jsonify({"error": "Brain graph service not initialized"}), 503
    
    try:
        # Get current brain graph stats
        brain_stats = _brain_graph_service.get_stats()
        
        # Calculate activity metrics
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=24)
        
        activity_metrics = {
            "events_24h": 0,
            "active_entities": 0,
            "top_entities": [],
            "activity_trend": "stable"
        }
        
        # Get event activity if available
        if _event_store:
            try:
                recent_events = _event_store.get_events_since(yesterday)
                activity_metrics["events_24h"] = len(recent_events)
                
                # Count unique entities
                entity_counts: Dict[str, int] = {}
                for event in recent_events[-500:]:  # Sample recent events
                    entity_id = event.get("entity_id")
                    if entity_id:
                        entity_counts[entity_id] = entity_counts.get(entity_id, 0) + 1
                
                activity_metrics["active_entities"] = len(entity_counts)
                
                # Top 5 most active entities
                top_entities = sorted(
                    entity_counts.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]
                activity_metrics["top_entities"] = [
                    {"entity_id": eid, "count": count} 
                    for eid, count in top_entities
                ]
                
            except Exception:
                # Graceful degradation if event store fails
                pass
        
        # Get candidate metrics
        candidate_metrics = {
            "pending": 0,
            "accepted_24h": 0,
            "dismissed_24h": 0,
            "detection_active": False
        }
        
        if _candidate_service:
            try:
                candidate_stats = _candidate_service.get_stats()
                candidate_metrics.update(candidate_stats)
            except Exception:
                # Graceful degradation
                pass
        
        # Calculate health score (0-100)
        health_score = _calculate_health_score(brain_stats, activity_metrics)
        
        # Determine status color
        if health_score >= 80:
            status_color = "green"
            status_text = "Healthy"
        elif health_score >= 60:
            status_color = "yellow"  
            status_text = "Active"
        elif health_score >= 30:
            status_color = "orange"
            status_text = "Learning"
        else:
            status_color = "red"
            status_text = "Initializing"
        
        return jsonify({
            "timestamp": now.isoformat(),
            "brain_graph": brain_stats,
            "activity": activity_metrics,
            "candidates": candidate_metrics,
            "health": {
                "score": health_score,
                "status": status_text,
                "color": status_color
            },
            "recommendations": _get_health_recommendations(brain_stats, activity_metrics)
        })
        
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@dashboard_bp.route('/quick-graph.svg', methods=['GET'])
@require_api_key
def get_quick_graph() -> Response:
    """
    Get a simplified brain graph visualization optimized for dashboard display.
    
    Query parameters:
    - size: small (default), medium, large
    """
    if not _brain_graph_service:
        error_svg = _generate_error_svg("Service unavailable")
        return Response(error_svg, mimetype='image/svg+xml'), 503
    
    try:
        size = request.args.get('size', 'small')
        
        # Size-specific limits
        size_config = {
            'small': {'nodes': 20, 'edges': 40, 'width': 300, 'height': 200},
            'medium': {'nodes': 50, 'edges': 100, 'width': 500, 'height': 350},
            'large': {'nodes': 80, 'edges': 200, 'width': 700, 'height': 500}
        }
        
        config = size_config.get(size, size_config['small'])
        
        # Get top nodes by activity/score
        graph_state = _brain_graph_service.get_graph_state(
            limit_nodes=config['nodes'],
            limit_edges=config['edges']
        )
        
        # Render with dashboard-optimized settings
        renderer = GraphRenderer()
        svg_bytes = renderer.render_svg(
            graph_state=graph_state,
            layout='neato',  # Better for small graphs
            theme='light',
            label_style='short'
        )
        
        return Response(svg_bytes, mimetype='image/svg+xml')
        
    except Exception as e:
        error_svg = _generate_error_svg(f"Render error: {str(e)[:40]}")
        return Response(error_svg, mimetype='image/svg+xml'), 500

def _calculate_health_score(brain_stats: Dict, activity_metrics: Dict) -> int:
    """Calculate overall brain graph health score (0-100)."""
    score = 0
    
    # Graph connectivity (30 points)
    nodes = brain_stats.get('nodes', 0)
    edges = brain_stats.get('edges', 0)
    
    if nodes > 0:
        score += min(30, nodes * 2)  # Up to 15 nodes = 30 points
        connectivity = edges / max(nodes, 1)
        score += min(10, connectivity * 5)  # Good connectivity bonus
    
    # Activity level (40 points)
    events_24h = activity_metrics.get('events_24h', 0)
    active_entities = activity_metrics.get('active_entities', 0)
    
    score += min(25, events_24h // 10)  # Up to 250 events = 25 points
    score += min(15, active_entities)   # Up to 15 entities = 15 points
    
    # System stability (30 points)
    # Base stability points (system running)
    score += 20
    
    # Bonus for balanced growth
    max_nodes = brain_stats.get('max_nodes', 500)
    if nodes < max_nodes * 0.8:  # Not hitting limits
        score += 10
    
    return min(100, score)

def _get_health_recommendations(brain_stats: Dict, activity_metrics: Dict) -> List[str]:
    """Generate actionable health recommendations."""
    recommendations = []
    
    nodes = brain_stats.get('nodes', 0)
    edges = brain_stats.get('edges', 0)
    events_24h = activity_metrics.get('events_24h', 0)
    active_entities = activity_metrics.get('active_entities', 0)
    
    if nodes == 0:
        recommendations.append("Enable event forwarding to start building the brain graph")
    elif nodes < 10:
        recommendations.append("Expand entity allowlist to capture more home activity")
    
    if events_24h < 50:
        recommendations.append("Check that event forwarder is active and receiving data")
    elif events_24h > 1000:
        recommendations.append("Consider filtering high-frequency entities to reduce noise")
    
    if edges == 0 and nodes > 5:
        recommendations.append("Wait for more activity to discover entity relationships")
    
    if active_entities < 5:
        recommendations.append("Add more zones or device types to entity allowlist")
    
    # If everything looks good
    if not recommendations and nodes > 20 and events_24h > 100:
        recommendations.append("Brain graph is healthy and learning your home patterns")
    
    return recommendations

def _generate_error_svg(message: str) -> str:
    """Generate a simple error SVG."""
    return f'''<?xml version="1.0"?>
<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6"/>
    <text x="150" y="90" text-anchor="middle" fill="#6c757d" font-size="12">
        Brain Graph
    </text>
    <text x="150" y="110" text-anchor="middle" fill="#dc3545" font-size="10">
        {message}
    </text>
</svg>'''