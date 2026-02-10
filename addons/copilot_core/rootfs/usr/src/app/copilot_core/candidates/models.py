"""
Candidates System - Data Models

Privacy-first automation candidate detection with bounded metadata.
"""
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum


class CandidateType(Enum):
    """Types of automation candidates."""
    AUTOMATION = "automation"
    SCENE = "scene"
    SCRIPT = "script"
    REPAIR = "repair"


class CandidateStatus(Enum):
    """Candidate lifecycle status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class ConfidenceLevel(Enum):
    """Confidence levels for candidates."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Evidence:
    """Privacy-first evidence for automation candidate."""
    pattern: str  # Anonymized pattern description
    frequency: int  # How often observed
    last_seen: float  # Timestamp
    confidence: float  # 0.0 - 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)  # Bounded to 1KB
    
    def __post_init__(self):
        """Validate evidence bounds."""
        # Ensure metadata is bounded
        metadata_str = json.dumps(self.metadata, sort_keys=True)
        if len(metadata_str) > 1024:  # 1KB limit
            raise ValueError(f"Evidence metadata exceeds 1KB: {len(metadata_str)} bytes")
        
        # Validate confidence bounds
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")


@dataclass  
class CandidateBlueprint:
    """Automation blueprint for candidate implementation."""
    type: CandidateType
    title: str
    description: str
    triggers: List[Dict[str, Any]]  # HA automation triggers
    conditions: List[Dict[str, Any]] = field(default_factory=list)  # Optional conditions
    actions: List[Dict[str, Any]] = field(default_factory=list)  # HA actions
    variables: Dict[str, Any] = field(default_factory=dict)  # Blueprint variables
    
    def __post_init__(self):
        """Validate blueprint structure."""
        if not self.triggers:
            raise ValueError("Blueprint must have at least one trigger")
        
        # Validate title length (for HA compatibility)
        if len(self.title) > 100:
            raise ValueError(f"Blueprint title too long: {len(self.title)} > 100")


@dataclass
class Candidate:
    """Automation candidate with privacy-first design."""
    candidate_id: str  # Deterministic hash of pattern
    type: CandidateType
    title: str
    description: str
    confidence: ConfidenceLevel
    score: float  # Composite score 0.0-1.0
    evidence: List[Evidence]
    blueprint: Optional[CandidateBlueprint] = None
    
    # Lifecycle
    status: CandidateStatus = CandidateStatus.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    
    # Decision tracking
    decision_reason: Optional[str] = None
    decision_at: Optional[float] = None
    
    @classmethod
    def generate_id(cls, pattern: str, type_: CandidateType) -> str:
        """Generate deterministic candidate ID from pattern."""
        content = f"{type_.value}:{pattern}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def __post_init__(self):
        """Validate candidate structure."""
        # Validate score bounds
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be 0.0-1.0, got {self.score}")
        
        # Validate title length  
        if len(self.title) > 200:
            raise ValueError(f"Candidate title too long: {len(self.title)} > 200")
        
        # Validate description length
        if len(self.description) > 1000:
            raise ValueError(f"Candidate description too long: {len(self.description)} > 1000")
        
        # Update timestamp
        self.updated_at = time.time()
    
    def is_expired(self) -> bool:
        """Check if candidate has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def accept(self, reason: Optional[str] = None) -> None:
        """Mark candidate as accepted."""
        self.status = CandidateStatus.ACCEPTED
        self.decision_at = time.time()
        self.decision_reason = reason
        self.updated_at = time.time()
    
    def dismiss(self, reason: Optional[str] = None) -> None:
        """Mark candidate as dismissed."""
        self.status = CandidateStatus.DISMISSED
        self.decision_at = time.time()
        self.decision_reason = reason
        self.updated_at = time.time()
    
    def expire(self) -> None:
        """Mark candidate as expired."""
        self.status = CandidateStatus.EXPIRED
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/storage."""
        result = asdict(self)
        # Convert enums to strings
        result['type'] = self.type.value
        result['confidence'] = self.confidence.value
        result['status'] = self.status.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candidate':
        """Create candidate from dictionary."""
        # Convert enum strings back to enums
        data['type'] = CandidateType(data['type'])
        data['confidence'] = ConfidenceLevel(data['confidence'])  
        data['status'] = CandidateStatus(data['status'])
        
        # Handle blueprint if present
        if data.get('blueprint'):
            bp_data = data['blueprint']
            bp_data['type'] = CandidateType(bp_data['type'])
            data['blueprint'] = CandidateBlueprint(**bp_data)
        
        # Handle evidence list
        if data.get('evidence'):
            data['evidence'] = [Evidence(**ev) for ev in data['evidence']]
        
        return cls(**data)


@dataclass
class CandidateStats:
    """Statistics for candidate system."""
    total_candidates: int = 0
    pending_candidates: int = 0
    accepted_candidates: int = 0
    dismissed_candidates: int = 0
    expired_candidates: int = 0
    
    # By type
    automation_candidates: int = 0
    scene_candidates: int = 0
    script_candidates: int = 0
    repair_candidates: int = 0
    
    # Time ranges
    candidates_24h: int = 0
    candidates_7d: int = 0
    
    # Quality metrics
    avg_confidence_score: float = 0.0
    high_confidence_count: int = 0
    
    def __post_init__(self):
        """Validate stats structure."""
        # Ensure non-negative counts
        for field_name, field_value in asdict(self).items():
            if isinstance(field_value, int) and field_value < 0:
                raise ValueError(f"Negative count for {field_name}: {field_value}")