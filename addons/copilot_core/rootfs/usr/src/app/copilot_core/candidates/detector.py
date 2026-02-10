"""
Candidates System - Pattern Detection

Privacy-first pattern detection for automation candidates using brain graph analysis.
"""
import time
from typing import List, Optional, Dict, Any, Set
from collections import defaultdict, Counter
import logging

from ..brain_graph.service import BrainGraphService
from .models import (
    Candidate, CandidateType, ConfidenceLevel, Evidence, 
    CandidateBlueprint
)

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects automation patterns from brain graph analysis."""
    
    def __init__(self, brain_graph: BrainGraphService):
        self.brain_graph = brain_graph
        
        # Configuration
        self.min_pattern_frequency = 3  # Minimum occurrences to consider
        self.pattern_window_hours = 168  # 7 days for pattern analysis
        self.confidence_thresholds = {
            ConfidenceLevel.HIGH: 0.8,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.LOW: 0.3
        }
    
    def detect_automation_candidates(self) -> List[Candidate]:
        """Detect automation candidates from recent patterns."""
        candidates = []
        
        try:
            # Analyze temporal patterns
            candidates.extend(self._detect_temporal_automations())
            
            # Analyze trigger-response patterns
            candidates.extend(self._detect_trigger_response_automations())
            
            # Analyze location-based patterns
            candidates.extend(self._detect_location_based_automations())
            
            # Analyze device state coordination patterns
            candidates.extend(self._detect_coordination_automations())
            
            logger.info(f"Detected {len(candidates)} automation candidates")
            
        except Exception as e:
            logger.error(f"Error detecting candidates: {e}")
        
        return candidates
    
    def _detect_temporal_automations(self) -> List[Candidate]:
        """Detect time-based automation patterns."""
        candidates = []
        
        # Get recent state changes from brain graph
        recent_nodes = self.brain_graph.get_nodes_by_kind("state_change", 
                                                         since_hours=self.pattern_window_hours)
        
        # Group by entity and analyze temporal patterns
        entity_patterns = defaultdict(list)
        for node in recent_nodes:
            if 'entity_id' in node.metadata:
                entity_id = node.metadata['entity_id']
                entity_patterns[entity_id].append({
                    'timestamp': node.updated_at,
                    'state': node.metadata.get('new_state'),
                    'domain': entity_id.split('.')[0] if '.' in entity_id else 'unknown'
                })
        
        # Analyze each entity's temporal patterns
        for entity_id, events in entity_patterns.items():
            if len(events) < self.min_pattern_frequency:
                continue
                
            # Sort by timestamp
            events.sort(key=lambda x: x['timestamp'])
            
            # Detect recurring time patterns
            time_patterns = self._find_time_patterns(events)
            
            for pattern in time_patterns:
                candidate = self._create_temporal_automation_candidate(
                    entity_id, pattern, events
                )
                if candidate:
                    candidates.append(candidate)
        
        return candidates
    
    def _detect_trigger_response_automations(self) -> List[Candidate]:
        """Detect trigger→response automation patterns."""
        candidates = []
        
        # Get recent service calls (intentional actions)
        service_nodes = self.brain_graph.get_nodes_by_kind("service_call",
                                                          since_hours=self.pattern_window_hours)
        
        # Get recent state changes  
        state_nodes = self.brain_graph.get_nodes_by_kind("state_change",
                                                        since_hours=self.pattern_window_hours)
        
        # Find temporal correlations between states and subsequent service calls
        correlations = self._find_temporal_correlations(state_nodes, service_nodes)
        
        for correlation in correlations:
            if correlation['frequency'] >= self.min_pattern_frequency:
                candidate = self._create_trigger_response_candidate(correlation)
                if candidate:
                    candidates.append(candidate)
        
        return candidates
    
    def _detect_location_based_automations(self) -> List[Candidate]:
        """Detect location/zone-based automation patterns."""
        candidates = []
        
        # Get nodes with zone information
        zone_nodes = self.brain_graph.get_nodes_with_metadata_key("zone_id",
                                                                 since_hours=self.pattern_window_hours)
        
        # Group by zone and analyze patterns
        zone_patterns = defaultdict(lambda: defaultdict(list))
        
        for node in zone_nodes:
            zone_id = node.metadata.get('zone_id')
            entity_id = node.metadata.get('entity_id')
            
            if zone_id and entity_id:
                zone_patterns[zone_id][entity_id].append({
                    'timestamp': node.updated_at,
                    'state': node.metadata.get('new_state'),
                    'kind': node.kind
                })
        
        # Analyze co-occurrence patterns within zones
        for zone_id, entities in zone_patterns.items():
            zone_candidates = self._analyze_zone_co_occurrences(zone_id, entities)
            candidates.extend(zone_candidates)
        
        return candidates
    
    def _detect_coordination_automations(self) -> List[Candidate]:
        """Detect device coordination patterns (e.g., lights following each other)."""
        candidates = []
        
        # Get entities of similar types
        light_nodes = self.brain_graph.get_nodes_by_kind("state_change",
                                                        since_hours=self.pattern_window_hours,
                                                        entity_domain="light")
        
        # Find coordination patterns
        coordination_patterns = self._find_coordination_patterns(light_nodes)
        
        for pattern in coordination_patterns:
            if pattern['frequency'] >= self.min_pattern_frequency:
                candidate = self._create_coordination_candidate(pattern)
                if candidate:
                    candidates.append(candidate)
        
        return candidates
    
    def _find_time_patterns(self, events: List[Dict]) -> List[Dict]:
        """Find recurring time patterns in events."""
        patterns = []
        
        # Extract hours and days of week
        time_data = []
        for event in events:
            timestamp = event['timestamp']
            dt = time.localtime(timestamp)
            time_data.append({
                'hour': dt.tm_hour,
                'weekday': dt.tm_wday,  # 0=Monday
                'state': event['state']
            })
        
        # Find most common hour patterns
        hour_counter = Counter()
        for data in time_data:
            if data['state'] == 'on':  # Focus on activation patterns
                hour_counter[data['hour']] += 1
        
        # Identify strong time patterns
        total_events = len([d for d in time_data if d['state'] == 'on'])
        for hour, count in hour_counter.most_common(3):
            frequency = count / total_events if total_events > 0 else 0
            
            if frequency > 0.4:  # More than 40% of activations at this hour
                patterns.append({
                    'type': 'time_based',
                    'hour': hour,
                    'frequency': frequency,
                    'count': count,
                    'confidence': min(frequency * 1.5, 1.0)  # Boost confidence for strong patterns
                })
        
        return patterns
    
    def _find_temporal_correlations(self, trigger_nodes: List, response_nodes: List) -> List[Dict]:
        """Find temporal correlations between triggers and responses."""
        correlations = []
        correlation_window = 300  # 5 minutes
        
        # Create correlation pairs
        correlation_counts = defaultdict(int)
        correlation_examples = defaultdict(list)
        
        for trigger in trigger_nodes:
            trigger_time = trigger.updated_at
            trigger_entity = trigger.metadata.get('entity_id', '')
            
            # Look for responses within the correlation window
            for response in response_nodes:
                response_time = response.updated_at
                response_service = response.metadata.get('service', '')
                
                # Skip if response is before trigger
                if response_time <= trigger_time:
                    continue
                
                # Check if within correlation window
                time_diff = response_time - trigger_time
                if time_diff <= correlation_window:
                    pattern_key = f"{trigger_entity}→{response_service}"
                    correlation_counts[pattern_key] += 1
                    correlation_examples[pattern_key].append({
                        'trigger_time': trigger_time,
                        'response_time': response_time,
                        'delay': time_diff
                    })
        
        # Convert to correlation objects
        for pattern_key, frequency in correlation_counts.items():
            if frequency >= self.min_pattern_frequency:
                examples = correlation_examples[pattern_key]
                avg_delay = sum(ex['delay'] for ex in examples) / len(examples)
                
                correlations.append({
                    'pattern': pattern_key,
                    'frequency': frequency,
                    'avg_delay': avg_delay,
                    'confidence': min(frequency / 10.0, 1.0),  # Normalize to 0-1
                    'examples': examples[:3]  # Keep a few examples
                })
        
        return correlations
    
    def _analyze_zone_co_occurrences(self, zone_id: str, entities: Dict) -> List[Candidate]:
        """Analyze co-occurrence patterns within a zone."""
        candidates = []
        
        # Find entities that often activate together
        activation_windows = []
        
        for entity_id, events in entities.items():
            for event in events:
                if event.get('state') == 'on':
                    activation_windows.append({
                        'entity_id': entity_id,
                        'timestamp': event['timestamp']
                    })
        
        # Sort by timestamp
        activation_windows.sort(key=lambda x: x['timestamp'])
        
        # Find co-activations within short time windows
        co_activation_window = 120  # 2 minutes
        co_activations = defaultdict(int)
        
        for i, activation in enumerate(activation_windows):
            # Look ahead for co-activations
            for j in range(i + 1, len(activation_windows)):
                next_activation = activation_windows[j]
                time_diff = next_activation['timestamp'] - activation['timestamp']
                
                if time_diff > co_activation_window:
                    break
                
                # Record co-activation
                entities_pair = tuple(sorted([activation['entity_id'], 
                                            next_activation['entity_id']]))
                co_activations[entities_pair] += 1
        
        # Create candidates for strong co-activation patterns
        for (entity1, entity2), frequency in co_activations.items():
            if frequency >= self.min_pattern_frequency:
                confidence_score = min(frequency / 10.0, 1.0)
                
                candidate = self._create_zone_coordination_candidate(
                    zone_id, entity1, entity2, frequency, confidence_score
                )
                if candidate:
                    candidates.append(candidate)
        
        return candidates
    
    def _find_coordination_patterns(self, nodes: List) -> List[Dict]:
        """Find coordination patterns between similar devices."""
        patterns = []
        
        # Group by zone for coordination analysis
        zone_entities = defaultdict(list)
        
        for node in nodes:
            zone_id = node.metadata.get('zone_id')
            entity_id = node.metadata.get('entity_id')
            
            if zone_id and entity_id:
                zone_entities[zone_id].append({
                    'entity_id': entity_id,
                    'timestamp': node.updated_at,
                    'state': node.metadata.get('new_state')
                })
        
        # Analyze coordination within each zone
        for zone_id, entities in zone_entities.items():
            if len(set(e['entity_id'] for e in entities)) < 2:
                continue  # Need at least 2 different entities
            
            # Sort by timestamp
            entities.sort(key=lambda x: x['timestamp'])
            
            # Find following patterns (entity A followed by entity B)
            following_patterns = defaultdict(int)
            follow_window = 60  # 1 minute
            
            for i, entity in enumerate(entities):
                if entity['state'] == 'on':
                    # Look for followers within window
                    for j in range(i + 1, len(entities)):
                        follower = entities[j]
                        time_diff = follower['timestamp'] - entity['timestamp']
                        
                        if time_diff > follow_window:
                            break
                        
                        if (follower['state'] == 'on' and 
                            follower['entity_id'] != entity['entity_id']):
                            
                            pattern_key = f"{entity['entity_id']}→{follower['entity_id']}"
                            following_patterns[pattern_key] += 1
            
            # Convert strong patterns to candidate data
            for pattern_key, frequency in following_patterns.items():
                if frequency >= self.min_pattern_frequency:
                    patterns.append({
                        'type': 'coordination',
                        'zone_id': zone_id,
                        'pattern': pattern_key,
                        'frequency': frequency,
                        'confidence': min(frequency / 8.0, 1.0)
                    })
        
        return patterns
    
    def _create_temporal_automation_candidate(self, entity_id: str, 
                                            pattern: Dict, events: List) -> Optional[Candidate]:
        """Create automation candidate for temporal patterns."""
        try:
            domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'
            hour = pattern['hour']
            frequency = pattern['frequency']
            
            # Generate deterministic ID
            pattern_desc = f"time_{domain}_{entity_id}_{hour:02d}h"
            candidate_id = Candidate.generate_id(pattern_desc, CandidateType.AUTOMATION)
            
            # Determine confidence level
            confidence = ConfidenceLevel.LOW
            if frequency >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
                confidence = ConfidenceLevel.HIGH
            elif frequency >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
                confidence = ConfidenceLevel.MEDIUM
            
            # Create evidence
            evidence = [Evidence(
                pattern=f"Entity activates at {hour:02d}:00",
                frequency=pattern['count'],
                last_seen=max(e['timestamp'] for e in events),
                confidence=pattern['confidence'],
                metadata={'hour': hour, 'entity_id': entity_id}
            )]
            
            # Create blueprint
            blueprint = CandidateBlueprint(
                type=CandidateType.AUTOMATION,
                title=f"Daily {domain.title()} Schedule",
                description=f"Turn on {entity_id} at {hour:02d}:00 daily",
                triggers=[{
                    'platform': 'time',
                    'at': f"{hour:02d}:00:00"
                }],
                actions=[{
                    'service': f'{domain}.turn_on',
                    'target': {'entity_id': entity_id}
                }]
            )
            
            return Candidate(
                candidate_id=candidate_id,
                type=CandidateType.AUTOMATION,
                title=f"Schedule {entity_id.replace('_', ' ').title()}",
                description=f"Automatically turn on {entity_id} at {hour:02d}:00 based on your usage pattern",
                confidence=confidence,
                score=frequency,
                evidence=evidence,
                blueprint=blueprint,
                expires_at=time.time() + 30 * 24 * 3600  # 30 days
            )
            
        except Exception as e:
            logger.error(f"Error creating temporal candidate: {e}")
            return None
    
    def _create_trigger_response_candidate(self, correlation: Dict) -> Optional[Candidate]:
        """Create automation candidate for trigger-response patterns."""
        try:
            pattern = correlation['pattern']
            frequency = correlation['frequency']
            avg_delay = correlation['avg_delay']
            
            # Parse pattern
            trigger_entity, response_service = pattern.split('→')
            
            # Generate deterministic ID
            candidate_id = Candidate.generate_id(pattern, CandidateType.AUTOMATION)
            
            # Determine confidence
            confidence_score = correlation['confidence']
            confidence = ConfidenceLevel.LOW
            if confidence_score >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
                confidence = ConfidenceLevel.HIGH
            elif confidence_score >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
                confidence = ConfidenceLevel.MEDIUM
            
            # Create evidence
            evidence = [Evidence(
                pattern=f"When {trigger_entity} changes, {response_service} follows",
                frequency=frequency,
                last_seen=time.time(),
                confidence=confidence_score,
                metadata={'avg_delay': avg_delay, 'trigger': trigger_entity, 'response': response_service}
            )]
            
            return Candidate(
                candidate_id=candidate_id,
                type=CandidateType.AUTOMATION,
                title=f"Auto-respond to {trigger_entity.replace('_', ' ').title()}",
                description=f"Automatically call {response_service} when {trigger_entity} changes state",
                confidence=confidence,
                score=confidence_score,
                evidence=evidence,
                expires_at=time.time() + 30 * 24 * 3600
            )
            
        except Exception as e:
            logger.error(f"Error creating trigger-response candidate: {e}")
            return None
    
    def _create_zone_coordination_candidate(self, zone_id: str, entity1: str, 
                                          entity2: str, frequency: int, 
                                          confidence_score: float) -> Optional[Candidate]:
        """Create automation candidate for zone coordination patterns."""
        try:
            pattern_desc = f"zone_coord_{zone_id}_{entity1}_{entity2}"
            candidate_id = Candidate.generate_id(pattern_desc, CandidateType.AUTOMATION)
            
            # Determine confidence
            confidence = ConfidenceLevel.LOW
            if confidence_score >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
                confidence = ConfidenceLevel.HIGH
            elif confidence_score >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
                confidence = ConfidenceLevel.MEDIUM
            
            # Create evidence
            evidence = [Evidence(
                pattern=f"Entities often activate together in {zone_id}",
                frequency=frequency,
                last_seen=time.time(),
                confidence=confidence_score,
                metadata={'zone_id': zone_id, 'entities': [entity1, entity2]}
            )]
            
            return Candidate(
                candidate_id=candidate_id,
                type=CandidateType.AUTOMATION,
                title=f"Coordinate {zone_id.replace('_', ' ').title()} Devices",
                description=f"When {entity1} turns on, also turn on {entity2}",
                confidence=confidence,
                score=confidence_score,
                evidence=evidence,
                expires_at=time.time() + 30 * 24 * 3600
            )
            
        except Exception as e:
            logger.error(f"Error creating zone coordination candidate: {e}")
            return None
    
    def _create_coordination_candidate(self, pattern: Dict) -> Optional[Candidate]:
        """Create automation candidate for coordination patterns."""
        try:
            pattern_key = pattern['pattern']
            frequency = pattern['frequency']
            confidence_score = pattern['confidence']
            
            # Parse pattern
            leader, follower = pattern_key.split('→')
            
            candidate_id = Candidate.generate_id(pattern_key, CandidateType.AUTOMATION)
            
            # Determine confidence
            confidence = ConfidenceLevel.LOW
            if confidence_score >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
                confidence = ConfidenceLevel.HIGH
            elif confidence_score >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
                confidence = ConfidenceLevel.MEDIUM
            
            # Create evidence
            evidence = [Evidence(
                pattern=f"Device coordination: {leader} → {follower}",
                frequency=frequency,
                last_seen=time.time(),
                confidence=confidence_score,
                metadata={'leader': leader, 'follower': follower}
            )]
            
            return Candidate(
                candidate_id=candidate_id,
                type=CandidateType.AUTOMATION,
                title=f"Follow Pattern: {follower.split('.')[-1].replace('_', ' ').title()}",
                description=f"When {leader} turns on, automatically turn on {follower}",
                confidence=confidence,
                score=confidence_score,
                evidence=evidence,
                expires_at=time.time() + 30 * 24 * 3600
            )
            
        except Exception as e:
            logger.error(f"Error creating coordination candidate: {e}")
            return None