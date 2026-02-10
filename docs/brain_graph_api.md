# Brain Graph API Documentation

## Overview

The Brain Graph API provides privacy-first knowledge graph functionality for the AI Home CoPilot Core Add-on. It maintains a bounded, time-decaying graph of relationships between entities, zones, devices, concepts, and events.

## Key Features

- **Privacy-First**: No raw HA attributes stored, automatic PII redaction
- **Bounded Storage**: Configurable limits (default: 500 nodes, 1500 edges)
- **Time Decay**: Exponential decay scoring (24h half-life for nodes, 12h for edges)
- **Real-time Visualization**: SVG graph snapshots and JSON state export
- **Thread-Safe**: Concurrent read/write operations supported

## API Endpoints

All endpoints require authentication via `X-API-Key` header.

### GET /api/v1/graph/state

Returns the current graph state as JSON.

**Query Parameters:**
- `max_nodes` (int, optional): Maximum nodes to return (default: 100, max: 500)
- `max_edges` (int, optional): Maximum edges to return (default: 200, max: 1500)
- `min_score` (float, optional): Minimum node score threshold (default: 0.1)
- `min_weight` (float, optional): Minimum edge weight threshold (default: 0.1)
- `kinds` (string, optional): Comma-separated node kinds to filter by

**Response:**
```json
{
  "timestamp": 1707565200000,
  "nodes": [
    {
      "id": "ha.entity:light.kitchen",
      "kind": "entity",
      "label": "Kitchen Light",
      "score": 0.85,
      "domain": "light",
      "tags": ["main_area"],
      "updated_at_ms": 1707564800000
    }
  ],
  "edges": [
    {
      "id": "light.kitchen|in_zone|zone:kitchen",
      "from": "ha.entity:light.kitchen",
      "to": "zone:kitchen",
      "type": "in_zone",
      "weight": 0.92,
      "updated_at_ms": 1707564800000
    }
  ],
  "stats": {
    "total_nodes": 42,
    "total_edges": 87,
    "returned_nodes": 42,
    "returned_edges": 87
  }
}
```

### GET /api/v1/graph/snapshot

Returns an SVG visualization of the graph.

**Query Parameters:**
- `max_nodes` (int, optional): Maximum nodes to include (default: 50, max: 200)
- `layout` (string, optional): Layout algorithm ("force", "hierarchical", "circular")
- `show_labels` (bool, optional): Include node labels (default: true)
- `show_weights` (bool, optional): Show edge weights (default: false)

**Response:**
- **Content-Type**: `image/svg+xml`
- **Body**: SVG XML document

### GET /api/v1/graph/stats

Returns graph statistics and health metrics.

**Response:**
```json
{
  "timestamp": 1707565200000,
  "counts": {
    "nodes": 42,
    "edges": 87,
    "nodes_by_kind": {
      "entity": 25,
      "zone": 8,
      "concept": 9
    },
    "edges_by_type": {
      "in_zone": 25,
      "affects": 35,
      "correlates": 27
    }
  },
  "scores": {
    "avg_node_score": 0.65,
    "max_node_score": 0.98,
    "avg_edge_weight": 0.42,
    "max_edge_weight": 0.87
  },
  "storage": {
    "db_size_bytes": 152432,
    "last_compaction": 1707564000000,
    "next_compaction": 1707567600000
  },
  "performance": {
    "last_query_ms": 12,
    "avg_query_ms": 15,
    "total_queries": 1847
  }
}
```

### POST /api/v1/graph/prune

Manually triggers graph pruning to remove low-scoring nodes and edges.

**Request Body:**
```json
{
  "min_node_score": 0.1,
  "min_edge_weight": 0.1,
  "dry_run": false
}
```

**Response:**
```json
{
  "timestamp": 1707565200000,
  "pruned": {
    "nodes": 3,
    "edges": 7
  },
  "remaining": {
    "nodes": 39,
    "edges": 80
  },
  "dry_run": false
}
```

## Data Models

### GraphNode
```
id: string              # Stable, namespaced identifier
kind: NodeKind         # entity|zone|device|person|concept|module|event
label: string          # Human-readable name
updated_at_ms: number  # Last update timestamp
score: number          # Current salience (0.0-1.0)
domain?: string        # For HA entities (light, sensor, etc.)
source?: object        # Source system metadata
tags?: string[]        # Short descriptive tags (no PII)
meta?: object          # Bounded metadata (max 2KB)
```

### GraphEdge
```
id: string              # Hash of from|type|to
from: string           # Source node ID
to: string             # Target node ID  
type: EdgeType         # Relationship type
updated_at_ms: number  # Last update timestamp
weight: number         # Current strength (0.0-1.0)
evidence?: object      # Evidence metadata
meta?: object          # Bounded metadata (max 2KB)
```

### Node Kinds
- `entity`: Home Assistant entities
- `zone`: Physical or logical zones
- `device`: Hardware devices
- `person`: People (privacy-safe IDs only)
- `concept`: Abstract concepts or states
- `module`: System modules or services
- `event`: Significant events or triggers

### Edge Types
- `in_zone`: Physical containment relationships
- `controls`: Control/command relationships
- `affects`: Influence relationships
- `correlates`: Statistical correlations
- `triggered_by`: Causation relationships
- `observed_with`: Co-occurrence patterns
- `mentions`: Contextual references

## Privacy & Security

### Automatic Redaction
All string values are automatically scanned and redacted for:
- Email addresses
- Phone numbers 
- IP addresses
- URLs
- API tokens (pattern-based detection)

### Bounded Storage
- **Node limit**: 500 (configurable)
- **Edge limit**: 1500 (configurable) 
- **Metadata size**: 2KB per node/edge
- **Total storage**: ~10MB typical

### Data Retention
- **Scoring decay**: Exponential with configurable half-life
- **Auto-pruning**: Low-scoring items removed during compaction
- **Manual control**: Explicit pruning API available

## Integration

The Brain Graph integrates with:
- **Event Processing**: HA state changes update graph
- **Tag System**: Tags applied to graph entities
- **Candidate System**: Uses graph for automation discovery
- **Health Monitoring**: Graph health included in system metrics

## Configuration

Add-on configuration options:
```json
{
  "brain_graph": {
    "enabled": true,
    "max_nodes": 500,
    "max_edges": 1500,
    "node_decay_hours": 24,
    "edge_decay_hours": 12,
    "compaction_interval_hours": 6,
    "svg_max_nodes": 50
  }
}
```

## Troubleshooting

### Common Issues

**Empty graph**: Check if event processing is enabled and HA state changes are being received.

**High memory usage**: Reduce `max_nodes`/`max_edges` limits or increase pruning frequency.

**Slow queries**: Enable database indices or reduce query result limits.

### Debug Endpoints

Use `/api/v1/graph/stats` to monitor:
- Query performance metrics
- Storage utilization
- Compaction status
- Node/edge distribution

### Logs

Brain Graph logs are prefixed with `[BrainGraph]` and include:
- Node/edge creation and updates
- Pruning operations and statistics
- Database compaction events
- Performance warnings

## Version History

- **v0.4.5**: Complete implementation with REST API
- **v0.4.4**: Integration with Candidates System
- **v0.4.3**: Basic graph operations and storage