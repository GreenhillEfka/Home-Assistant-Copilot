#!/usr/bin/env python3
"""
Test candidates store functionality.
"""
import tempfile
import time
import os
from unittest import TestCase

from copilot_core.candidates.store import CandidateStore
from copilot_core.candidates.models import (
    Candidate, Evidence, CandidateBlueprint, CandidateType, 
    CandidateStatus, ConfidenceLevel
)


class TestCandidateStore(TestCase):
    
    def setUp(self):
        """Set up test store with temporary database."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        
        self.store = CandidateStore(
            db_path=self.temp_file.name,
            max_candidates=10  # Small limit for testing
        )
        
        # Create test data
        self.evidence = [Evidence(
            pattern="test pattern",
            frequency=3,
            last_seen=time.time(),
            confidence=0.7
        )]
        
        self.blueprint = CandidateBlueprint(
            type=CandidateType.AUTOMATION,
            title="Test Blueprint",
            description="Test",
            triggers=[{"platform": "time"}]
        )
    
    def tearDown(self):
        """Clean up temporary database."""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_store_and_retrieve_candidate(self):
        """Test storing and retrieving a candidate."""
        candidate = Candidate(
            candidate_id="test_id_1",
            type=CandidateType.AUTOMATION,
            title="Test Candidate",
            description="Test description",
            confidence=ConfidenceLevel.MEDIUM,
            score=0.75,
            evidence=self.evidence,
            blueprint=self.blueprint
        )
        
        # Store candidate
        stored = self.store.store_candidate(candidate)
        self.assertTrue(stored)
        
        # Retrieve candidate
        retrieved = self.store.get_candidate("test_id_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.candidate_id, "test_id_1")
        self.assertEqual(retrieved.title, "Test Candidate")
        self.assertEqual(retrieved.type, CandidateType.AUTOMATION)
        self.assertEqual(retrieved.confidence, ConfidenceLevel.MEDIUM)
        self.assertEqual(retrieved.score, 0.75)
        self.assertEqual(len(retrieved.evidence), 1)
        self.assertIsNotNone(retrieved.blueprint)
    
    def test_store_duplicate_candidate(self):
        """Test storing duplicate candidates."""
        candidate = Candidate(
            candidate_id="duplicate_id",
            type=CandidateType.AUTOMATION,
            title="Test",
            description="Test",
            confidence=ConfidenceLevel.MEDIUM,
            score=0.5,
            evidence=self.evidence
        )
        
        # First store should succeed
        stored1 = self.store.store_candidate(candidate)
        self.assertTrue(stored1)
        
        # Second store should fail (duplicate)
        stored2 = self.store.store_candidate(candidate)
        self.assertFalse(stored2)
    
    def test_get_nonexistent_candidate(self):
        """Test retrieving non-existent candidate."""
        retrieved = self.store.get_candidate("nonexistent_id")
        self.assertIsNone(retrieved)
    
    def test_list_candidates_basic(self):
        """Test basic candidate listing."""
        # Store multiple candidates
        for i in range(3):
            candidate = Candidate(
                candidate_id=f"list_test_{i}",
                type=CandidateType.AUTOMATION,
                title=f"Test {i}",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=0.5 + (i * 0.1),
                evidence=self.evidence
            )
            self.store.store_candidate(candidate)
        
        # List all candidates
        candidates = self.store.list_candidates()
        self.assertEqual(len(candidates), 3)
        
        # Should be ordered by score DESC
        scores = [c.score for c in candidates]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_list_candidates_with_filters(self):
        """Test candidate listing with filters."""
        # Store candidates with different properties
        candidates_data = [
            ("auto_1", CandidateType.AUTOMATION, CandidateStatus.PENDING, 0.8),
            ("auto_2", CandidateType.AUTOMATION, CandidateStatus.ACCEPTED, 0.7),
            ("scene_1", CandidateType.SCENE, CandidateStatus.PENDING, 0.6),
            ("auto_3", CandidateType.AUTOMATION, CandidateStatus.DISMISSED, 0.5)
        ]
        
        for cid, ctype, status, score in candidates_data:
            candidate = Candidate(
                candidate_id=cid,
                type=ctype,
                title="Test",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=score,
                evidence=self.evidence,
                status=status
            )
            self.store.store_candidate(candidate)
        
        # Filter by status
        pending = self.store.list_candidates(status=CandidateStatus.PENDING)
        self.assertEqual(len(pending), 2)
        
        # Filter by type
        automations = self.store.list_candidates(type_=CandidateType.AUTOMATION)
        self.assertEqual(len(automations), 3)
        
        # Filter by min_score
        high_score = self.store.list_candidates(min_score=0.7)
        self.assertEqual(len(high_score), 2)
        
        # Combined filters
        pending_automations = self.store.list_candidates(
            status=CandidateStatus.PENDING,
            type_=CandidateType.AUTOMATION
        )
        self.assertEqual(len(pending_automations), 1)
        self.assertEqual(pending_automations[0].candidate_id, "auto_1")
    
    def test_list_candidates_with_limit(self):
        """Test candidate listing with limit."""
        # Store 5 candidates
        for i in range(5):
            candidate = Candidate(
                candidate_id=f"limit_test_{i}",
                type=CandidateType.AUTOMATION,
                title=f"Test {i}",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=0.5,
                evidence=self.evidence
            )
            self.store.store_candidate(candidate)
        
        # List with limit
        candidates = self.store.list_candidates(limit=3)
        self.assertEqual(len(candidates), 3)
    
    def test_update_candidate_status(self):
        """Test updating candidate status."""
        candidate = Candidate(
            candidate_id="status_test",
            type=CandidateType.AUTOMATION,
            title="Test",
            description="Test",
            confidence=ConfidenceLevel.MEDIUM,
            score=0.5,
            evidence=self.evidence
        )
        self.store.store_candidate(candidate)
        
        # Update status to accepted
        updated = self.store.update_candidate_status(
            "status_test",
            CandidateStatus.ACCEPTED,
            "Test reason"
        )
        self.assertTrue(updated)
        
        # Verify update
        retrieved = self.store.get_candidate("status_test")
        self.assertEqual(retrieved.status, CandidateStatus.ACCEPTED)
        self.assertEqual(retrieved.decision_reason, "Test reason")
        self.assertIsNotNone(retrieved.decision_at)
        
        # Try to update non-existent candidate
        not_updated = self.store.update_candidate_status(
            "nonexistent",
            CandidateStatus.ACCEPTED
        )
        self.assertFalse(not_updated)
    
    def test_expire_candidates(self):
        """Test candidate expiration."""
        now = time.time()
        
        # Store candidates with different expiration times
        candidates_data = [
            ("expire_1", now - 3600),  # Expired 1 hour ago
            ("expire_2", now + 3600),  # Expires in 1 hour
            ("expire_3", None),        # No expiration
            ("expire_4", now - 1800)   # Expired 30 min ago
        ]
        
        for cid, expires_at in candidates_data:
            candidate = Candidate(
                candidate_id=cid,
                type=CandidateType.AUTOMATION,
                title="Test",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=0.5,
                evidence=self.evidence,
                expires_at=expires_at
            )
            self.store.store_candidate(candidate)
        
        # Run expiration
        expired_count = self.store.expire_candidates()
        self.assertEqual(expired_count, 2)  # Two were expired
        
        # Check that expired candidates are marked as expired
        expired1 = self.store.get_candidate("expire_1")
        self.assertEqual(expired1.status, CandidateStatus.EXPIRED)
        
        expired4 = self.store.get_candidate("expire_4")
        self.assertEqual(expired4.status, CandidateStatus.EXPIRED)
        
        # Check that non-expired candidates are still pending
        not_expired = self.store.get_candidate("expire_2")
        self.assertEqual(not_expired.status, CandidateStatus.PENDING)
    
    def test_prune_old_candidates(self):
        """Test pruning old candidates."""
        old_time = time.time() - (200 * 24 * 3600)  # 200 days ago
        recent_time = time.time() - (100 * 24 * 3600)  # 100 days ago
        
        # Store old decided candidates
        old_candidates = [
            ("old_accepted", CandidateStatus.ACCEPTED, old_time),
            ("old_dismissed", CandidateStatus.DISMISSED, old_time),
            ("old_expired", CandidateStatus.EXPIRED, old_time),
            ("recent_accepted", CandidateStatus.ACCEPTED, recent_time),
            ("pending", CandidateStatus.PENDING, old_time)  # Should not be pruned
        ]
        
        for cid, status, updated_at in old_candidates:
            candidate = Candidate(
                candidate_id=cid,
                type=CandidateType.AUTOMATION,
                title="Test",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=0.5,
                evidence=self.evidence,
                status=status,
                updated_at=updated_at,
                decision_at=updated_at if status in [CandidateStatus.ACCEPTED, CandidateStatus.DISMISSED, CandidateStatus.EXPIRED] else None
            )
            self.store.store_candidate(candidate)
        
        # Prune candidates older than 180 days
        pruned_count = self.store.prune_candidates(older_than_days=180)
        self.assertGreaterEqual(pruned_count, 2)  # At least two old decided candidates
        
        # Verify remaining candidates
        remaining = self.store.list_candidates(limit=100)
        remaining_ids = [c.candidate_id for c in remaining]
        
        self.assertIn("recent_accepted", remaining_ids)
        self.assertIn("pending", remaining_ids)
        self.assertNotIn("old_accepted", remaining_ids)
        self.assertNotIn("old_dismissed", remaining_ids)
        self.assertNotIn("old_expired", remaining_ids)
    
    def test_capacity_enforcement(self):
        """Test capacity enforcement (max_candidates)."""
        # Store candidates up to the limit (10)
        for i in range(12):  # More than limit
            candidate = Candidate(
                candidate_id=f"capacity_test_{i:02d}",
                type=CandidateType.AUTOMATION,
                title=f"Test {i}",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=0.5,
                evidence=self.evidence,
                created_at=time.time() + i  # Later candidates have later timestamps
            )
            self.store.store_candidate(candidate)
        
        # Check that we don't exceed the limit
        all_candidates = self.store.list_candidates(limit=100)
        self.assertLessEqual(len(all_candidates), 10)
        
        # The newest candidates should be kept
        candidate_ids = [c.candidate_id for c in all_candidates]
        # Should contain the later candidates (higher indices)
        self.assertIn("capacity_test_11", candidate_ids)
        # Should not contain the earliest candidates
        self.assertNotIn("capacity_test_00", candidate_ids)
    
    def test_get_stats(self):
        """Test statistics generation."""
        now = time.time()
        day_ago = now - 24 * 3600
        week_ago = now - 7 * 24 * 3600
        
        # Store candidates with different properties
        test_data = [
            ("pending_auto", CandidateType.AUTOMATION, CandidateStatus.PENDING, ConfidenceLevel.HIGH, 0.9, now),
            ("accepted_auto", CandidateType.AUTOMATION, CandidateStatus.ACCEPTED, ConfidenceLevel.MEDIUM, 0.7, day_ago),
            ("dismissed_scene", CandidateType.SCENE, CandidateStatus.DISMISSED, ConfidenceLevel.LOW, 0.3, week_ago),
            ("expired_repair", CandidateType.REPAIR, CandidateStatus.EXPIRED, ConfidenceLevel.HIGH, 0.8, now),
            ("high_conf_script", CandidateType.SCRIPT, CandidateStatus.PENDING, ConfidenceLevel.HIGH, 0.95, now)
        ]
        
        for cid, ctype, status, confidence, score, created_at in test_data:
            candidate = Candidate(
                candidate_id=cid,
                type=ctype,
                title="Test",
                description="Test",
                confidence=confidence,
                score=score,
                evidence=self.evidence,
                status=status,
                created_at=created_at
            )
            self.store.store_candidate(candidate)
        
        # Get stats
        stats = self.store.get_stats()
        
        # Check counts by status
        self.assertEqual(stats.total_candidates, 5)
        self.assertEqual(stats.pending_candidates, 2)
        self.assertEqual(stats.accepted_candidates, 1)
        self.assertEqual(stats.dismissed_candidates, 1)
        self.assertEqual(stats.expired_candidates, 1)
        
        # Check counts by type
        self.assertEqual(stats.automation_candidates, 2)
        self.assertEqual(stats.scene_candidates, 1)
        self.assertEqual(stats.script_candidates, 1)
        self.assertEqual(stats.repair_candidates, 1)
        
        # Check time-based counts  
        # Note: due to timing precision, we check >= instead of exact equality
        self.assertGreaterEqual(stats.candidates_24h, 2)  # At least 2 created today
        self.assertGreaterEqual(stats.candidates_7d, 4)   # At least 4 created within a week
        
        # Check quality metrics
        self.assertEqual(stats.high_confidence_count, 3)  # 3 high confidence candidates
        # Average score should be reasonable (scores: 0.9, 0.7, 0.3, 0.8, 0.95)
        self.assertGreater(stats.avg_confidence_score, 0.7)
        self.assertLess(stats.avg_confidence_score, 1.0)


if __name__ == '__main__':
    import unittest
    unittest.main()