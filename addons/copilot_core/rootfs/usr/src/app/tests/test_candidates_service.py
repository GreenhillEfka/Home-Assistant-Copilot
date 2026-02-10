#!/usr/bin/env python3
"""
Test candidates service functionality.
"""
import tempfile
import time
import os
from unittest import TestCase
from unittest.mock import Mock, patch

from copilot_core.candidates.service import CandidateService
from copilot_core.candidates.models import (
    Candidate, Evidence, CandidateType, CandidateStatus, ConfidenceLevel
)


class TestCandidateService(TestCase):
    
    def setUp(self):
        """Set up test service with mocked dependencies."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        
        # Mock brain graph service
        self.mock_brain_graph = Mock()
        
        # Create service with temporary database
        self.service = CandidateService(
            brain_graph=self.mock_brain_graph,
            db_path=self.temp_file.name,
            max_candidates=20
        )
        
        # Reduce detection interval for testing
        self.service.detection_interval = 0  # No interval for testing
    
    def tearDown(self):
        """Clean up temporary database."""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service.store)
        self.assertIsNotNone(self.service.detector)
        self.assertEqual(self.service.brain_graph, self.mock_brain_graph)
        self.assertTrue(self.service.auto_expire_enabled)
    
    def test_detect_and_store_candidates_no_detection_needed(self):
        """Test detection skipping when interval not reached."""
        # Set last detection to recent time
        self.service._last_detection = time.time()
        self.service.detection_interval = 3600  # 1 hour
        
        # Should skip detection
        count = self.service.detect_and_store_candidates(force=False)
        self.assertEqual(count, 0)
    
    @patch('copilot_core.candidates.service.PatternDetector')
    def test_detect_and_store_candidates_with_results(self, mock_detector_class):
        """Test successful detection and storage."""
        # Mock detector
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Create mock candidates
        mock_candidates = [
            Candidate(
                candidate_id="mock_1",
                type=CandidateType.AUTOMATION,
                title="Mock Candidate 1",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=0.7,
                evidence=[Evidence("pattern1", 3, time.time(), 0.7)]
            ),
            Candidate(
                candidate_id="mock_2", 
                type=CandidateType.SCENE,
                title="Mock Candidate 2",
                description="Test",
                confidence=ConfidenceLevel.HIGH,
                score=0.8,
                evidence=[Evidence("pattern2", 5, time.time(), 0.8)]
            )
        ]
        
        mock_detector.detect_automation_candidates.return_value = mock_candidates
        self.service.detector = mock_detector
        
        # Run detection
        count = self.service.detect_and_store_candidates(force=True)
        
        # Verify results
        self.assertEqual(count, 2)
        
        # Verify candidates were stored
        stored_1 = self.service.get_candidate("mock_1")
        stored_2 = self.service.get_candidate("mock_2")
        
        self.assertIsNotNone(stored_1)
        self.assertIsNotNone(stored_2)
        self.assertEqual(stored_1.title, "Mock Candidate 1")
        self.assertEqual(stored_2.title, "Mock Candidate 2")
    
    @patch('copilot_core.candidates.service.PatternDetector')
    def test_detect_and_store_candidates_with_duplicates(self, mock_detector_class):
        """Test detection with duplicate candidates."""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Pre-store a candidate
        existing_candidate = Candidate(
            candidate_id="existing_1",
            type=CandidateType.AUTOMATION,
            title="Existing",
            description="Test",
            confidence=ConfidenceLevel.MEDIUM,
            score=0.6,
            evidence=[Evidence("pattern", 2, time.time(), 0.6)]
        )
        self.service.store.store_candidate(existing_candidate)
        
        # Mock detector returns the same candidate (duplicate)
        mock_detector.detect_automation_candidates.return_value = [existing_candidate]
        self.service.detector = mock_detector
        
        # Run detection
        count = self.service.detect_and_store_candidates(force=True)
        
        # Should not store duplicate
        self.assertEqual(count, 0)
    
    def test_get_candidate(self):
        """Test candidate retrieval."""
        # Store a test candidate
        candidate = Candidate(
            candidate_id="get_test",
            type=CandidateType.AUTOMATION,
            title="Get Test",
            description="Test",
            confidence=ConfidenceLevel.MEDIUM,
            score=0.5,
            evidence=[Evidence("pattern", 1, time.time(), 0.5)]
        )
        self.service.store.store_candidate(candidate)
        
        # Retrieve candidate
        retrieved = self.service.get_candidate("get_test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.candidate_id, "get_test")
        
        # Try to get non-existent candidate
        not_found = self.service.get_candidate("nonexistent")
        self.assertIsNone(not_found)
    
    def test_list_candidates(self):
        """Test candidate listing."""
        # Store test candidates
        candidates_data = [
            ("list_1", CandidateStatus.PENDING, 0.8),
            ("list_2", CandidateStatus.ACCEPTED, 0.7),
            ("list_3", CandidateStatus.PENDING, 0.6)
        ]
        
        for cid, status, score in candidates_data:
            candidate = Candidate(
                candidate_id=cid,
                type=CandidateType.AUTOMATION,
                title=f"Test {cid}",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=score,
                evidence=[Evidence("pattern", 1, time.time(), score)],
                status=status
            )
            self.service.store.store_candidate(candidate)
        
        # List all candidates
        all_candidates = self.service.list_candidates()
        self.assertEqual(len(all_candidates), 3)
        
        # List only pending candidates
        pending = self.service.list_candidates(status=CandidateStatus.PENDING)
        self.assertEqual(len(pending), 2)
        
        # List with min score
        high_score = self.service.list_candidates(min_score=0.7)
        self.assertEqual(len(high_score), 2)
    
    def test_accept_candidate(self):
        """Test candidate acceptance."""
        # Store a test candidate
        candidate = Candidate(
            candidate_id="accept_test",
            type=CandidateType.AUTOMATION,
            title="Accept Test",
            description="Test",
            confidence=ConfidenceLevel.MEDIUM,
            score=0.7,
            evidence=[Evidence("pattern", 2, time.time(), 0.7)]
        )
        self.service.store.store_candidate(candidate)
        
        # Accept the candidate
        success = self.service.accept_candidate("accept_test", "Good idea!")
        self.assertTrue(success)
        
        # Verify acceptance
        updated = self.service.get_candidate("accept_test")
        self.assertEqual(updated.status, CandidateStatus.ACCEPTED)
        self.assertEqual(updated.decision_reason, "Good idea!")
        self.assertIsNotNone(updated.decision_at)
        
        # Try to accept non-existent candidate
        fail = self.service.accept_candidate("nonexistent")
        self.assertFalse(fail)
    
    def test_dismiss_candidate(self):
        """Test candidate dismissal."""
        # Store a test candidate
        candidate = Candidate(
            candidate_id="dismiss_test",
            type=CandidateType.AUTOMATION,
            title="Dismiss Test",
            description="Test",
            confidence=ConfidenceLevel.MEDIUM,
            score=0.4,
            evidence=[Evidence("pattern", 1, time.time(), 0.4)]
        )
        self.service.store.store_candidate(candidate)
        
        # Dismiss the candidate
        success = self.service.dismiss_candidate("dismiss_test", "Not useful")
        self.assertTrue(success)
        
        # Verify dismissal
        updated = self.service.get_candidate("dismiss_test")
        self.assertEqual(updated.status, CandidateStatus.DISMISSED)
        self.assertEqual(updated.decision_reason, "Not useful")
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        # Store test candidates with different properties
        candidates_data = [
            ("stats_1", CandidateStatus.PENDING, ConfidenceLevel.HIGH, 0.9),
            ("stats_2", CandidateStatus.ACCEPTED, ConfidenceLevel.MEDIUM, 0.7),
            ("stats_3", CandidateStatus.DISMISSED, ConfidenceLevel.LOW, 0.3),
            ("stats_4", CandidateStatus.PENDING, ConfidenceLevel.HIGH, 0.8)
        ]
        
        for cid, status, confidence, score in candidates_data:
            candidate = Candidate(
                candidate_id=cid,
                type=CandidateType.AUTOMATION,
                title=f"Test {cid}",
                description="Test",
                confidence=confidence,
                score=score,
                evidence=[Evidence("pattern", 1, time.time(), score)],
                status=status
            )
            self.service.store.store_candidate(candidate)
        
        # Get stats
        stats = self.service.get_stats()
        
        self.assertEqual(stats.total_candidates, 4)
        self.assertEqual(stats.pending_candidates, 2)
        self.assertEqual(stats.accepted_candidates, 1)
        self.assertEqual(stats.dismissed_candidates, 1)
    
    def test_force_detection(self):
        """Test force detection method."""
        with patch.object(self.service, 'detect_and_store_candidates') as mock_detect:
            mock_detect.return_value = 3  # Mock 3 new candidates
            
            result = self.service.force_detection()
            
            self.assertTrue(result['success'])
            self.assertEqual(result['new_candidates'], 3)
            self.assertIn('total_pending', result)
            self.assertIn('timestamp', result)
            
            # Verify force=True was passed
            mock_detect.assert_called_once_with(force=True)
    
    def test_get_high_confidence_candidates(self):
        """Test high confidence candidate retrieval."""
        # Store candidates with different confidence scores
        candidates_data = [
            ("high_1", 0.9, ConfidenceLevel.HIGH),
            ("high_2", 0.8, ConfidenceLevel.HIGH),
            ("medium_1", 0.6, ConfidenceLevel.MEDIUM),
            ("low_1", 0.3, ConfidenceLevel.LOW)
        ]
        
        for cid, score, confidence in candidates_data:
            candidate = Candidate(
                candidate_id=cid,
                type=CandidateType.AUTOMATION,
                title=f"Test {cid}",
                description="Test",
                confidence=confidence,
                score=score,
                evidence=[Evidence("pattern", 1, time.time(), score)]
            )
            self.service.store.store_candidate(candidate)
        
        # Get high confidence candidates
        high_confidence = self.service.get_high_confidence_candidates()
        
        # Should only return candidates with score >= 0.7
        self.assertEqual(len(high_confidence), 2)
        scores = [c.score for c in high_confidence]
        self.assertTrue(all(score >= 0.7 for score in scores))
    
    def test_get_candidate_summary(self):
        """Test candidate summary generation."""
        candidate = Candidate(
            candidate_id="summary_test",
            type=CandidateType.SCENE,
            title="Summary Test",
            description="Test description",
            confidence=ConfidenceLevel.HIGH,
            score=0.85,
            evidence=[Evidence("pattern", 3, time.time(), 0.85)]
        )
        self.service.store.store_candidate(candidate)
        
        # Get summary
        summary = self.service.get_candidate_summary("summary_test")
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary['candidate_id'], "summary_test")
        self.assertEqual(summary['type'], "scene")
        self.assertEqual(summary['title'], "Summary Test")
        self.assertEqual(summary['confidence'], "high")
        self.assertEqual(summary['score'], 0.85)
        self.assertEqual(summary['evidence_count'], 1)
        self.assertFalse(summary['has_blueprint'])  # No blueprint in this test
        
        # Try non-existent candidate
        no_summary = self.service.get_candidate_summary("nonexistent")
        self.assertIsNone(no_summary)
    
    def test_bulk_dismiss_low_confidence(self):
        """Test bulk dismissal of low confidence candidates."""
        # Store candidates with different scores
        scores = [0.2, 0.3, 0.4, 0.6, 0.8]
        
        for i, score in enumerate(scores):
            candidate = Candidate(
                candidate_id=f"bulk_test_{i}",
                type=CandidateType.AUTOMATION,
                title=f"Test {i}",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=score,
                evidence=[Evidence("pattern", 1, time.time(), score)]
            )
            self.service.store.store_candidate(candidate)
        
        # Bulk dismiss candidates with score <= 0.3
        dismissed_count = self.service.bulk_dismiss_low_confidence(max_score=0.3)
        self.assertEqual(dismissed_count, 2)  # Two candidates with score <= 0.3
        
        # Verify dismissals
        dismissed_1 = self.service.get_candidate("bulk_test_0")  # score 0.2
        dismissed_2 = self.service.get_candidate("bulk_test_1")  # score 0.3
        not_dismissed = self.service.get_candidate("bulk_test_2")  # score 0.4
        
        self.assertEqual(dismissed_1.status, CandidateStatus.DISMISSED)
        self.assertEqual(dismissed_2.status, CandidateStatus.DISMISSED)
        self.assertEqual(not_dismissed.status, CandidateStatus.PENDING)
    
    def test_enforce_pending_limit(self):
        """Test enforcement of pending candidate limit."""
        # Set low limit for testing
        self.service.max_pending_candidates = 3
        
        # Store more pending candidates than the limit
        for i in range(5):
            candidate = Candidate(
                candidate_id=f"limit_test_{i}",
                type=CandidateType.AUTOMATION,
                title=f"Test {i}",
                description="Test",
                confidence=ConfidenceLevel.MEDIUM,
                score=0.1 + (i * 0.1),  # Increasing scores
                evidence=[Evidence("pattern", 1, time.time(), 0.5)]
            )
            self.service.store.store_candidate(candidate)
        
        # Trigger limit enforcement
        self.service._enforce_pending_limit()
        
        # Should have dismissed the lowest scoring candidates
        pending = self.service.list_candidates(status=CandidateStatus.PENDING)
        self.assertLessEqual(len(pending), 3)
        
        # Highest scoring candidates should remain
        remaining_scores = [c.score for c in pending]
        self.assertTrue(all(score >= 0.3 for score in remaining_scores))
    
    def test_get_detection_status(self):
        """Test detection status information."""
        status = self.service.get_detection_status()
        
        self.assertIn('last_detection', status)
        self.assertIn('next_detection', status)
        self.assertIn('seconds_until_next', status)
        self.assertIn('detection_interval', status)
        self.assertIn('auto_expire_enabled', status)
        self.assertIn('max_pending_candidates', status)
        
        self.assertEqual(status['detection_interval'], self.service.detection_interval)
        self.assertEqual(status['auto_expire_enabled'], True)


if __name__ == '__main__':
    import unittest
    unittest.main()