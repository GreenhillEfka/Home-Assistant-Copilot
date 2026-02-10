#!/usr/bin/env python3
"""
Test candidates system models.
"""
import time
import json
from unittest import TestCase

from copilot_core.candidates.models import (
    Evidence, CandidateBlueprint, Candidate, CandidateStats,
    CandidateType, CandidateStatus, ConfidenceLevel
)


class TestEvidence(TestCase):
    
    def test_evidence_creation(self):
        """Test evidence creation with valid data."""
        evidence = Evidence(
            pattern="Light turns on at 18:00",
            frequency=5,
            last_seen=time.time(),
            confidence=0.8
        )
        
        self.assertEqual(evidence.pattern, "Light turns on at 18:00")
        self.assertEqual(evidence.frequency, 5)
        self.assertEqual(evidence.confidence, 0.8)
        self.assertEqual(evidence.metadata, {})
    
    def test_evidence_with_metadata(self):
        """Test evidence with metadata."""
        metadata = {"hour": 18, "entity_id": "light.living_room"}
        evidence = Evidence(
            pattern="Temporal pattern",
            frequency=3,
            last_seen=time.time(),
            confidence=0.7,
            metadata=metadata
        )
        
        self.assertEqual(evidence.metadata, metadata)
    
    def test_evidence_metadata_size_limit(self):
        """Test evidence metadata size limit (1KB)."""
        # Create metadata that exceeds 1KB
        large_metadata = {"data": "x" * 1100}  # > 1KB
        
        with self.assertRaises(ValueError) as cm:
            Evidence(
                pattern="Test",
                frequency=1,
                last_seen=time.time(),
                confidence=0.5,
                metadata=large_metadata
            )
        
        self.assertIn("exceeds 1KB", str(cm.exception))
    
    def test_evidence_confidence_bounds(self):
        """Test evidence confidence validation."""
        # Valid confidence
        evidence = Evidence("test", 1, time.time(), 0.5)
        self.assertEqual(evidence.confidence, 0.5)
        
        # Invalid confidence - too low
        with self.assertRaises(ValueError):
            Evidence("test", 1, time.time(), -0.1)
        
        # Invalid confidence - too high  
        with self.assertRaises(ValueError):
            Evidence("test", 1, time.time(), 1.1)


class TestCandidateBlueprint(TestCase):
    
    def test_blueprint_creation(self):
        """Test blueprint creation."""
        blueprint = CandidateBlueprint(
            type=CandidateType.AUTOMATION,
            title="Test Automation",
            description="Test description",
            triggers=[{"platform": "time", "at": "18:00:00"}],
            actions=[{"service": "light.turn_on", "target": {"entity_id": "light.test"}}]
        )
        
        self.assertEqual(blueprint.type, CandidateType.AUTOMATION)
        self.assertEqual(blueprint.title, "Test Automation")
        self.assertEqual(len(blueprint.triggers), 1)
        self.assertEqual(len(blueprint.actions), 1)
        self.assertEqual(blueprint.conditions, [])
        self.assertEqual(blueprint.variables, {})
    
    def test_blueprint_no_triggers_validation(self):
        """Test blueprint validation requires triggers."""
        with self.assertRaises(ValueError) as cm:
            CandidateBlueprint(
                type=CandidateType.AUTOMATION,
                title="Test",
                description="Test",
                triggers=[]  # Empty triggers should fail
            )
        
        self.assertIn("must have at least one trigger", str(cm.exception))
    
    def test_blueprint_title_length_validation(self):
        """Test blueprint title length limit."""
        long_title = "x" * 101  # > 100 chars
        
        with self.assertRaises(ValueError) as cm:
            CandidateBlueprint(
                type=CandidateType.AUTOMATION,
                title=long_title,
                description="Test",
                triggers=[{"platform": "time"}]
            )
        
        self.assertIn("title too long", str(cm.exception))


class TestCandidate(TestCase):
    
    def setUp(self):
        """Set up test data."""
        self.evidence = [Evidence("test pattern", 3, time.time(), 0.7)]
        self.blueprint = CandidateBlueprint(
            type=CandidateType.AUTOMATION,
            title="Test Blueprint",
            description="Test",
            triggers=[{"platform": "time"}]
        )
    
    def test_candidate_creation(self):
        """Test candidate creation."""
        candidate_id = Candidate.generate_id("test_pattern", CandidateType.AUTOMATION)
        
        candidate = Candidate(
            candidate_id=candidate_id,
            type=CandidateType.AUTOMATION,
            title="Test Candidate",
            description="Test description",
            confidence=ConfidenceLevel.MEDIUM,
            score=0.75,
            evidence=self.evidence,
            blueprint=self.blueprint
        )
        
        self.assertEqual(candidate.candidate_id, candidate_id)
        self.assertEqual(candidate.type, CandidateType.AUTOMATION)
        self.assertEqual(candidate.status, CandidateStatus.PENDING)
        self.assertEqual(candidate.confidence, ConfidenceLevel.MEDIUM)
        self.assertEqual(candidate.score, 0.75)
        self.assertIsNone(candidate.expires_at)
        self.assertIsNone(candidate.decision_reason)
    
    def test_candidate_id_generation(self):
        """Test deterministic candidate ID generation."""
        id1 = Candidate.generate_id("same_pattern", CandidateType.AUTOMATION)
        id2 = Candidate.generate_id("same_pattern", CandidateType.AUTOMATION)
        id3 = Candidate.generate_id("different_pattern", CandidateType.AUTOMATION)
        
        self.assertEqual(id1, id2)  # Same pattern = same ID
        self.assertNotEqual(id1, id3)  # Different pattern = different ID
        self.assertEqual(len(id1), 16)  # Should be 16 chars
    
    def test_candidate_score_validation(self):
        """Test candidate score bounds validation."""
        # Valid score
        candidate = Candidate(
            candidate_id="test",
            type=CandidateType.AUTOMATION,
            title="Test",
            description="Test",
            confidence=ConfidenceLevel.MEDIUM,
            score=0.5,
            evidence=self.evidence
        )
        self.assertEqual(candidate.score, 0.5)
        
        # Invalid scores
        with self.assertRaises(ValueError):
            Candidate(
                candidate_id="test", type=CandidateType.AUTOMATION,
                title="Test", description="Test", confidence=ConfidenceLevel.MEDIUM,
                score=-0.1, evidence=self.evidence
            )
        
        with self.assertRaises(ValueError):
            Candidate(
                candidate_id="test", type=CandidateType.AUTOMATION,
                title="Test", description="Test", confidence=ConfidenceLevel.MEDIUM,
                score=1.1, evidence=self.evidence
            )
    
    def test_candidate_title_length_validation(self):
        """Test candidate title length limit."""
        long_title = "x" * 201  # > 200 chars
        
        with self.assertRaises(ValueError) as cm:
            Candidate(
                candidate_id="test",
                type=CandidateType.AUTOMATION,
                title=long_title,
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=0.5,
                evidence=self.evidence
            )
        
        self.assertIn("title too long", str(cm.exception))
    
    def test_candidate_description_length_validation(self):
        """Test candidate description length limit."""
        long_description = "x" * 1001  # > 1000 chars
        
        with self.assertRaises(ValueError) as cm:
            Candidate(
                candidate_id="test",
                type=CandidateType.AUTOMATION,
                title="Test",
                description=long_description,
                confidence=ConfidenceLevel.MEDIUM,
                score=0.5,
                evidence=self.evidence
            )
        
        self.assertIn("description too long", str(cm.exception))
    
    def test_candidate_expiration(self):
        """Test candidate expiration logic."""
        now = time.time()
        
        # Not expired (no expiration set)
        candidate1 = Candidate(
            candidate_id="test1", type=CandidateType.AUTOMATION,
            title="Test", description="Test", confidence=ConfidenceLevel.MEDIUM,
            score=0.5, evidence=self.evidence
        )
        self.assertFalse(candidate1.is_expired())
        
        # Not expired (future expiration)
        candidate2 = Candidate(
            candidate_id="test2", type=CandidateType.AUTOMATION,
            title="Test", description="Test", confidence=ConfidenceLevel.MEDIUM,
            score=0.5, evidence=self.evidence, expires_at=now + 3600
        )
        self.assertFalse(candidate2.is_expired())
        
        # Expired (past expiration)
        candidate3 = Candidate(
            candidate_id="test3", type=CandidateType.AUTOMATION,
            title="Test", description="Test", confidence=ConfidenceLevel.MEDIUM,
            score=0.5, evidence=self.evidence, expires_at=now - 3600
        )
        self.assertTrue(candidate3.is_expired())
    
    def test_candidate_accept(self):
        """Test candidate acceptance."""
        candidate = Candidate(
            candidate_id="test", type=CandidateType.AUTOMATION,
            title="Test", description="Test", confidence=ConfidenceLevel.MEDIUM,
            score=0.5, evidence=self.evidence
        )
        
        self.assertEqual(candidate.status, CandidateStatus.PENDING)
        self.assertIsNone(candidate.decision_at)
        self.assertIsNone(candidate.decision_reason)
        
        candidate.accept("Looks good!")
        
        self.assertEqual(candidate.status, CandidateStatus.ACCEPTED)
        self.assertIsNotNone(candidate.decision_at)
        self.assertEqual(candidate.decision_reason, "Looks good!")
    
    def test_candidate_dismiss(self):
        """Test candidate dismissal."""
        candidate = Candidate(
            candidate_id="test", type=CandidateType.AUTOMATION,
            title="Test", description="Test", confidence=ConfidenceLevel.MEDIUM,
            score=0.5, evidence=self.evidence
        )
        
        candidate.dismiss("Not useful")
        
        self.assertEqual(candidate.status, CandidateStatus.DISMISSED)
        self.assertIsNotNone(candidate.decision_at)
        self.assertEqual(candidate.decision_reason, "Not useful")
    
    def test_candidate_expire(self):
        """Test candidate expiration."""
        candidate = Candidate(
            candidate_id="test", type=CandidateType.AUTOMATION,
            title="Test", description="Test", confidence=ConfidenceLevel.MEDIUM,
            score=0.5, evidence=self.evidence
        )
        
        candidate.expire()
        
        self.assertEqual(candidate.status, CandidateStatus.EXPIRED)
    
    def test_candidate_to_dict(self):
        """Test candidate serialization."""
        candidate = Candidate(
            candidate_id="test_id",
            type=CandidateType.AUTOMATION,
            title="Test",
            description="Test description",
            confidence=ConfidenceLevel.HIGH,
            score=0.8,
            evidence=self.evidence,
            blueprint=self.blueprint
        )
        
        data = candidate.to_dict()
        
        self.assertEqual(data['candidate_id'], "test_id")
        self.assertEqual(data['type'], "automation")
        self.assertEqual(data['confidence'], "high")
        self.assertEqual(data['status'], "pending")
        self.assertEqual(data['score'], 0.8)
        self.assertIsInstance(data['evidence'], list)
        self.assertIsInstance(data['blueprint'], dict)
    
    def test_candidate_from_dict(self):
        """Test candidate deserialization."""
        data = {
            'candidate_id': 'test_id',
            'type': 'automation',
            'title': 'Test',
            'description': 'Test description',
            'confidence': 'high',
            'score': 0.8,
            'status': 'pending',
            'created_at': time.time(),
            'updated_at': time.time(),
            'expires_at': None,
            'decision_at': None,
            'decision_reason': None,
            'evidence': [{
                'pattern': 'test pattern',
                'frequency': 3,
                'last_seen': time.time(),
                'confidence': 0.7,
                'metadata': {}
            }],
            'blueprint': {
                'type': 'automation',
                'title': 'Test Blueprint',
                'description': 'Test',
                'triggers': [{'platform': 'time'}],
                'conditions': [],
                'actions': [],
                'variables': {}
            }
        }
        
        candidate = Candidate.from_dict(data)
        
        self.assertEqual(candidate.candidate_id, 'test_id')
        self.assertEqual(candidate.type, CandidateType.AUTOMATION)
        self.assertEqual(candidate.confidence, ConfidenceLevel.HIGH)
        self.assertEqual(candidate.status, CandidateStatus.PENDING)
        self.assertEqual(len(candidate.evidence), 1)
        self.assertIsNotNone(candidate.blueprint)


class TestCandidateStats(TestCase):
    
    def test_stats_creation(self):
        """Test stats creation with defaults."""
        stats = CandidateStats()
        
        self.assertEqual(stats.total_candidates, 0)
        self.assertEqual(stats.pending_candidates, 0)
        self.assertEqual(stats.avg_confidence_score, 0.0)
    
    def test_stats_with_values(self):
        """Test stats with custom values."""
        stats = CandidateStats(
            total_candidates=10,
            pending_candidates=5,
            accepted_candidates=3,
            dismissed_candidates=2,
            automation_candidates=7,
            avg_confidence_score=0.75
        )
        
        self.assertEqual(stats.total_candidates, 10)
        self.assertEqual(stats.pending_candidates, 5)
        self.assertEqual(stats.avg_confidence_score, 0.75)
    
    def test_stats_negative_validation(self):
        """Test stats validation for negative values."""
        with self.assertRaises(ValueError):
            CandidateStats(total_candidates=-1)


if __name__ == '__main__':
    import unittest
    unittest.main()