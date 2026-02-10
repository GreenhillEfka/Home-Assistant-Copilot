"""
Candidates System - Storage Layer

Thread-safe SQLite storage for automation candidates with bounded capacity.
"""
import sqlite3
import json
import time
import threading
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import Candidate, CandidateStats, CandidateStatus, CandidateType, ConfidenceLevel


class CandidateStore:
    """Thread-safe SQLite storage for automation candidates."""
    
    def __init__(self, db_path: str = "/data/candidates.db", max_candidates: int = 1000):
        self.db_path = db_path
        self.max_candidates = max_candidates
        self._lock = threading.RLock()
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS candidates (
                        candidate_id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        confidence TEXT NOT NULL,
                        score REAL NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        expires_at REAL,
                        decision_at REAL,
                        decision_reason TEXT,
                        evidence_json TEXT NOT NULL,
                        blueprint_json TEXT
                    )
                """)
                
                # Indexes for common queries
                conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON candidates(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON candidates(type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON candidates(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_score ON candidates(score)")
                
                conn.commit()
            finally:
                conn.close()
    
    def store_candidate(self, candidate: Candidate) -> bool:
        """Store a candidate. Returns True if stored, False if duplicate."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Check if already exists
                cursor = conn.execute(
                    "SELECT candidate_id FROM candidates WHERE candidate_id = ?",
                    (candidate.candidate_id,)
                )
                if cursor.fetchone():
                    return False  # Already exists
                
                # Enforce capacity limit by removing oldest pending/expired
                self._enforce_capacity(conn)
                
                # Store candidate
                evidence_json = json.dumps([ev.__dict__ for ev in candidate.evidence])
                blueprint_json = None
                if candidate.blueprint:
                    blueprint_dict = candidate.blueprint.__dict__.copy()
                    blueprint_dict['type'] = candidate.blueprint.type.value  # Convert enum to string
                    blueprint_json = json.dumps(blueprint_dict)
                
                conn.execute("""
                    INSERT INTO candidates (
                        candidate_id, type, title, description, confidence, score,
                        status, created_at, updated_at, expires_at, decision_at, 
                        decision_reason, evidence_json, blueprint_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    candidate.candidate_id,
                    candidate.type.value,
                    candidate.title,
                    candidate.description,
                    candidate.confidence.value,
                    candidate.score,
                    candidate.status.value,
                    candidate.created_at,
                    candidate.updated_at,
                    candidate.expires_at,
                    candidate.decision_at,
                    candidate.decision_reason,
                    evidence_json,
                    blueprint_json
                ))
                
                conn.commit()
                return True
                
            finally:
                conn.close()
    
    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Retrieve a candidate by ID."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    "SELECT * FROM candidates WHERE candidate_id = ?",
                    (candidate_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._row_to_candidate(row)
                
            finally:
                conn.close()
    
    def list_candidates(self, 
                       status: Optional[CandidateStatus] = None,
                       type_: Optional[CandidateType] = None,
                       min_score: Optional[float] = None,
                       limit: int = 100) -> List[Candidate]:
        """List candidates with optional filtering."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                query = "SELECT * FROM candidates WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status.value)
                
                if type_:
                    query += " AND type = ?"
                    params.append(type_.value)
                
                if min_score is not None:
                    query += " AND score >= ?"
                    params.append(min_score)
                
                query += " ORDER BY score DESC, created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_candidate(row) for row in rows]
                
            finally:
                conn.close()
    
    def update_candidate_status(self, candidate_id: str, 
                              status: CandidateStatus,
                              decision_reason: Optional[str] = None) -> bool:
        """Update candidate status. Returns True if updated."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                decision_at = time.time() if status in [CandidateStatus.ACCEPTED, CandidateStatus.DISMISSED] else None
                
                cursor = conn.execute("""
                    UPDATE candidates 
                    SET status = ?, updated_at = ?, decision_at = ?, decision_reason = ?
                    WHERE candidate_id = ?
                """, (
                    status.value,
                    time.time(),
                    decision_at,
                    decision_reason,
                    candidate_id
                ))
                
                conn.commit()
                return cursor.rowcount > 0
                
            finally:
                conn.close()
    
    def expire_candidates(self) -> int:
        """Mark expired candidates as expired. Returns count of expired."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                now = time.time()
                cursor = conn.execute("""
                    UPDATE candidates 
                    SET status = 'expired', updated_at = ?
                    WHERE expires_at IS NOT NULL AND expires_at < ? AND status = 'pending'
                """, (now, now))
                
                conn.commit()
                return cursor.rowcount
                
            finally:
                conn.close()
    
    def prune_candidates(self, older_than_days: int = 180) -> int:
        """Remove old decided/expired candidates. Returns count removed."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cutoff = time.time() - (older_than_days * 24 * 3600)
                cursor = conn.execute("""
                    DELETE FROM candidates 
                    WHERE status IN ('accepted', 'dismissed', 'expired') 
                    AND (
                        (decision_at IS NOT NULL AND decision_at < ?) OR 
                        (decision_at IS NULL AND updated_at < ?)
                    )
                """, (cutoff, cutoff))
                
                conn.commit()
                return cursor.rowcount
                
            finally:
                conn.close()
    
    def get_stats(self) -> CandidateStats:
        """Get candidate statistics."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                stats = CandidateStats()
                
                # Total counts by status
                cursor = conn.execute("SELECT status, COUNT(*) FROM candidates GROUP BY status")
                for status, count in cursor.fetchall():
                    if status == 'pending':
                        stats.pending_candidates = count
                    elif status == 'accepted':
                        stats.accepted_candidates = count
                    elif status == 'dismissed':
                        stats.dismissed_candidates = count
                    elif status == 'expired':
                        stats.expired_candidates = count
                
                stats.total_candidates = (stats.pending_candidates + stats.accepted_candidates + 
                                        stats.dismissed_candidates + stats.expired_candidates)
                
                # Counts by type
                cursor = conn.execute("SELECT type, COUNT(*) FROM candidates GROUP BY type")
                for type_, count in cursor.fetchall():
                    if type_ == 'automation':
                        stats.automation_candidates = count
                    elif type_ == 'scene':
                        stats.scene_candidates = count
                    elif type_ == 'script':
                        stats.script_candidates = count
                    elif type_ == 'repair':
                        stats.repair_candidates = count
                
                # Time-based counts
                now = time.time()
                day_ago = now - 24 * 3600
                week_ago = now - 7 * 24 * 3600
                
                cursor = conn.execute("SELECT COUNT(*) FROM candidates WHERE created_at >= ?", (day_ago,))
                stats.candidates_24h = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM candidates WHERE created_at >= ?", (week_ago,))
                stats.candidates_7d = cursor.fetchone()[0]
                
                # Quality metrics
                cursor = conn.execute("SELECT AVG(score), COUNT(*) FROM candidates WHERE confidence = 'high'")
                row = cursor.fetchone()
                if row[0] is not None:
                    stats.avg_confidence_score = round(row[0], 3)
                stats.high_confidence_count = row[1] or 0
                
                return stats
                
            finally:
                conn.close()
    
    def _enforce_capacity(self, conn: sqlite3.Connection):
        """Remove oldest candidates to stay within capacity limit."""
        cursor = conn.execute("SELECT COUNT(*) FROM candidates")
        current_count = cursor.fetchone()[0]
        
        if current_count >= self.max_candidates:
            # Remove oldest pending/expired candidates first, then decided ones
            to_remove = current_count - self.max_candidates + 1
            
            conn.execute("""
                DELETE FROM candidates WHERE candidate_id IN (
                    SELECT candidate_id FROM candidates 
                    WHERE status IN ('pending', 'expired')
                    ORDER BY created_at ASC 
                    LIMIT ?
                )
            """, (to_remove,))
            
            # If still over limit, remove oldest decided candidates
            cursor = conn.execute("SELECT COUNT(*) FROM candidates")
            current_count = cursor.fetchone()[0]
            
            if current_count >= self.max_candidates:
                remaining_to_remove = current_count - self.max_candidates + 1
                conn.execute("""
                    DELETE FROM candidates WHERE candidate_id IN (
                        SELECT candidate_id FROM candidates 
                        ORDER BY created_at ASC 
                        LIMIT ?
                    )
                """, (remaining_to_remove,))
    
    def _row_to_candidate(self, row) -> Candidate:
        """Convert database row to Candidate object."""
        from .models import Evidence, CandidateBlueprint
        
        # Parse evidence JSON
        evidence_data = json.loads(row[12])  # evidence_json
        evidence = [Evidence(**ev) for ev in evidence_data]
        
        # Parse blueprint JSON if present
        blueprint = None
        if row[13]:  # blueprint_json
            blueprint_data = json.loads(row[13])
            blueprint_data['type'] = CandidateType(blueprint_data['type'])
            blueprint = CandidateBlueprint(**blueprint_data)
        
        return Candidate(
            candidate_id=row[0],
            type=CandidateType(row[1]),
            title=row[2],
            description=row[3],
            confidence=ConfidenceLevel(row[4]),
            score=row[5],
            status=CandidateStatus(row[6]),
            created_at=row[7],
            updated_at=row[8],
            expires_at=row[9],
            decision_at=row[10],
            decision_reason=row[11],
            evidence=evidence,
            blueprint=blueprint
        )