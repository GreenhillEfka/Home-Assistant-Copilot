"""
Candidates System - Service Layer

Main service coordinating candidate detection, storage, and lifecycle management.
"""
import time
import threading
import logging
from typing import List, Optional, Dict, Any

from .models import Candidate, CandidateStats, CandidateStatus, CandidateType
from .store import CandidateStore
from .detector import PatternDetector
from ..brain_graph.service import BrainGraphService

logger = logging.getLogger(__name__)


class CandidateService:
    """Main service for automation candidate management."""
    
    def __init__(self, 
                 brain_graph: BrainGraphService,
                 db_path: str = "/data/candidates.db",
                 max_candidates: int = 1000):
        self.brain_graph = brain_graph
        self.store = CandidateStore(db_path, max_candidates)
        self.detector = PatternDetector(brain_graph)
        
        self._lock = threading.RLock()
        self._last_detection = 0
        self.detection_interval = 3600  # 1 hour between detections
        
        # Configuration
        self.auto_expire_enabled = True
        self.max_pending_candidates = 50  # Limit active candidates
        
        logger.info("CandidateService initialized")
    
    def detect_and_store_candidates(self, force: bool = False) -> int:
        """Run detection and store new candidates. Returns count of new candidates."""
        with self._lock:
            now = time.time()
            
            # Check if detection interval has passed
            if not force and (now - self._last_detection) < self.detection_interval:
                logger.debug("Detection interval not reached, skipping")
                return 0
            
            try:
                logger.info("Starting candidate detection")
                
                # Run pattern detection
                new_candidates = self.detector.detect_automation_candidates()
                
                # Store new candidates (duplicates are ignored)
                stored_count = 0
                for candidate in new_candidates:
                    if self.store.store_candidate(candidate):
                        stored_count += 1
                        logger.info(f"Stored new candidate: {candidate.title}")
                
                # Cleanup old/expired candidates
                self._cleanup_candidates()
                
                # Enforce pending candidate limit
                self._enforce_pending_limit()
                
                self._last_detection = now
                logger.info(f"Detection complete: {stored_count} new candidates stored")
                
                return stored_count
                
            except Exception as e:
                logger.error(f"Error during candidate detection: {e}")
                return 0
    
    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Get a specific candidate by ID."""
        return self.store.get_candidate(candidate_id)
    
    def list_candidates(self, 
                       status: Optional[CandidateStatus] = None,
                       type_: Optional[CandidateType] = None,
                       min_score: Optional[float] = None,
                       limit: int = 50) -> List[Candidate]:
        """List candidates with optional filtering."""
        # Auto-expire before listing
        if self.auto_expire_enabled:
            self.store.expire_candidates()
        
        return self.store.list_candidates(status, type_, min_score, limit)
    
    def accept_candidate(self, candidate_id: str, reason: Optional[str] = None) -> bool:
        """Accept a candidate for implementation."""
        success = self.store.update_candidate_status(
            candidate_id, CandidateStatus.ACCEPTED, reason
        )
        
        if success:
            logger.info(f"Candidate {candidate_id} accepted: {reason}")
        
        return success
    
    def dismiss_candidate(self, candidate_id: str, reason: Optional[str] = None) -> bool:
        """Dismiss a candidate."""
        success = self.store.update_candidate_status(
            candidate_id, CandidateStatus.DISMISSED, reason
        )
        
        if success:
            logger.info(f"Candidate {candidate_id} dismissed: {reason}")
        
        return success
    
    def get_stats(self) -> CandidateStats:
        """Get candidate statistics."""
        return self.store.get_stats()
    
    def prune_old_candidates(self, older_than_days: int = 180) -> int:
        """Remove old decided/expired candidates."""
        count = self.store.prune_candidates(older_than_days)
        if count > 0:
            logger.info(f"Pruned {count} old candidates")
        return count
    
    def force_detection(self) -> Dict[str, Any]:
        """Force immediate candidate detection (for manual triggers)."""
        try:
            count = self.detect_and_store_candidates(force=True)
            stats = self.get_stats()
            
            return {
                "success": True,
                "new_candidates": count,
                "total_pending": stats.pending_candidates,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Force detection failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_high_confidence_candidates(self, limit: int = 10) -> List[Candidate]:
        """Get high-confidence pending candidates."""
        return self.list_candidates(
            status=CandidateStatus.PENDING,
            min_score=0.7,  # High confidence threshold
            limit=limit
        )
    
    def get_candidate_summary(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get a compact summary of a candidate (for API responses)."""
        candidate = self.get_candidate(candidate_id)
        if not candidate:
            return None
        
        return {
            "candidate_id": candidate.candidate_id,
            "type": candidate.type.value,
            "title": candidate.title,
            "description": candidate.description,
            "confidence": candidate.confidence.value,
            "score": candidate.score,
            "status": candidate.status.value,
            "created_at": candidate.created_at,
            "evidence_count": len(candidate.evidence),
            "has_blueprint": candidate.blueprint is not None,
            "expires_at": candidate.expires_at
        }
    
    def bulk_dismiss_low_confidence(self, max_score: float = 0.3) -> int:
        """Bulk dismiss low-confidence candidates."""
        with self._lock:
            low_confidence = self.list_candidates(
                status=CandidateStatus.PENDING,
                limit=1000  # Large limit to get all
            )
            
            dismissed_count = 0
            for candidate in low_confidence:
                if candidate.score <= max_score:
                    if self.dismiss_candidate(
                        candidate.candidate_id, 
                        f"Auto-dismissed: low confidence score {candidate.score}"
                    ):
                        dismissed_count += 1
            
            logger.info(f"Bulk dismissed {dismissed_count} low-confidence candidates")
            return dismissed_count
    
    def _cleanup_candidates(self):
        """Internal cleanup of expired candidates."""
        try:
            # Mark expired candidates as expired
            expired_count = self.store.expire_candidates()
            if expired_count > 0:
                logger.info(f"Marked {expired_count} candidates as expired")
            
        except Exception as e:
            logger.error(f"Error during candidate cleanup: {e}")
    
    def _enforce_pending_limit(self):
        """Enforce limit on pending candidates by dismissing oldest/lowest score."""
        try:
            pending = self.list_candidates(status=CandidateStatus.PENDING, limit=1000)
            
            if len(pending) > self.max_pending_candidates:
                # Sort by score (ascending) to dismiss lowest scores first
                pending.sort(key=lambda c: (c.score, c.created_at))
                
                to_dismiss = len(pending) - self.max_pending_candidates
                for i in range(to_dismiss):
                    candidate = pending[i]
                    self.dismiss_candidate(
                        candidate.candidate_id,
                        f"Auto-dismissed: pending limit exceeded (score: {candidate.score})"
                    )
                
                logger.info(f"Enforced pending limit: dismissed {to_dismiss} candidates")
                
        except Exception as e:
            logger.error(f"Error enforcing pending limit: {e}")
    
    def get_detection_status(self) -> Dict[str, Any]:
        """Get detection system status."""
        now = time.time()
        next_detection = self._last_detection + self.detection_interval
        
        return {
            "last_detection": self._last_detection,
            "next_detection": next_detection,
            "seconds_until_next": max(0, int(next_detection - now)),
            "detection_interval": self.detection_interval,
            "auto_expire_enabled": self.auto_expire_enabled,
            "max_pending_candidates": self.max_pending_candidates
        }