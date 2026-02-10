"""
Candidates System API

REST API for automation candidate management.
"""
from flask import Blueprint, request, jsonify
import logging

from ...candidates.service import CandidateService
from ...candidates.models import CandidateStatus, CandidateType
from ..security import require_token

logger = logging.getLogger(__name__)

# Global service instance (initialized by main.py)
candidate_service: CandidateService = None


def create_candidates_blueprint() -> Blueprint:
    """Create candidates API blueprint."""
    bp = Blueprint('candidates', __name__, url_prefix='/api/v1/candidates')
    
    @bp.route('/detection/trigger', methods=['POST'])
    @require_token
    def trigger_detection():
        """Manually trigger candidate detection."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            result = candidate_service.force_detection()
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Detection trigger failed: {e}")
            return jsonify({"error": "Detection failed"}), 500
    
    @bp.route('/detection/status', methods=['GET'])
    @require_token
    def get_detection_status():
        """Get detection system status."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            status = candidate_service.get_detection_status()
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Get detection status failed: {e}")
            return jsonify({"error": "Status check failed"}), 500
    
    @bp.route('/', methods=['GET'])
    @require_token
    def list_candidates():
        """List candidates with optional filtering."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            # Parse query parameters
            status_str = request.args.get('status')
            type_str = request.args.get('type')
            min_score = request.args.get('min_score', type=float)
            limit = request.args.get('limit', 50, type=int)
            summary_only = request.args.get('summary', 'false').lower() == 'true'
            
            # Convert string parameters to enums
            status = None
            if status_str:
                try:
                    status = CandidateStatus(status_str)
                except ValueError:
                    return jsonify({"error": f"Invalid status: {status_str}"}), 400
            
            type_ = None
            if type_str:
                try:
                    type_ = CandidateType(type_str)
                except ValueError:
                    return jsonify({"error": f"Invalid type: {type_str}"}), 400
            
            # Validate limits
            if limit > 200:
                limit = 200  # Enforce maximum limit
            
            # Get candidates
            candidates = candidate_service.list_candidates(status, type_, min_score, limit)
            
            # Return summary or full data
            if summary_only:
                result = []
                for candidate in candidates:
                    summary = candidate_service.get_candidate_summary(candidate.candidate_id)
                    if summary:
                        result.append(summary)
                return jsonify({"candidates": result, "count": len(result)})
            else:
                return jsonify({
                    "candidates": [c.to_dict() for c in candidates],
                    "count": len(candidates)
                })
                
        except Exception as e:
            logger.error(f"List candidates failed: {e}")
            return jsonify({"error": "List failed"}), 500
    
    @bp.route('/<candidate_id>', methods=['GET'])
    @require_token
    def get_candidate(candidate_id: str):
        """Get a specific candidate by ID."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            candidate = candidate_service.get_candidate(candidate_id)
            if not candidate:
                return jsonify({"error": "Candidate not found"}), 404
            
            return jsonify(candidate.to_dict())
            
        except Exception as e:
            logger.error(f"Get candidate failed: {e}")
            return jsonify({"error": "Retrieval failed"}), 500
    
    @bp.route('/<candidate_id>/accept', methods=['POST'])
    @require_token
    def accept_candidate(candidate_id: str):
        """Accept a candidate for implementation."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            data = request.get_json() or {}
            reason = data.get('reason', 'Accepted via API')
            
            success = candidate_service.accept_candidate(candidate_id, reason)
            if not success:
                return jsonify({"error": "Candidate not found or already decided"}), 404
            
            # Return updated candidate
            candidate = candidate_service.get_candidate(candidate_id)
            return jsonify({
                "success": True,
                "candidate": candidate.to_dict() if candidate else None
            })
            
        except Exception as e:
            logger.error(f"Accept candidate failed: {e}")
            return jsonify({"error": "Accept failed"}), 500
    
    @bp.route('/<candidate_id>/dismiss', methods=['POST'])
    @require_token
    def dismiss_candidate(candidate_id: str):
        """Dismiss a candidate."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            data = request.get_json() or {}
            reason = data.get('reason', 'Dismissed via API')
            
            success = candidate_service.dismiss_candidate(candidate_id, reason)
            if not success:
                return jsonify({"error": "Candidate not found or already decided"}), 404
            
            # Return updated candidate
            candidate = candidate_service.get_candidate(candidate_id)
            return jsonify({
                "success": True,
                "candidate": candidate.to_dict() if candidate else None
            })
            
        except Exception as e:
            logger.error(f"Dismiss candidate failed: {e}")
            return jsonify({"error": "Dismiss failed"}), 500
    
    @bp.route('/high-confidence', methods=['GET'])
    @require_token
    def get_high_confidence_candidates():
        """Get high-confidence pending candidates."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            limit = request.args.get('limit', 10, type=int)
            if limit > 50:
                limit = 50
            
            candidates = candidate_service.get_high_confidence_candidates(limit)
            
            return jsonify({
                "candidates": [c.to_dict() for c in candidates],
                "count": len(candidates)
            })
            
        except Exception as e:
            logger.error(f"Get high confidence candidates failed: {e}")
            return jsonify({"error": "Retrieval failed"}), 500
    
    @bp.route('/stats', methods=['GET'])
    @require_token
    def get_candidate_stats():
        """Get candidate system statistics."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            stats = candidate_service.get_stats()
            detection_status = candidate_service.get_detection_status()
            
            return jsonify({
                "stats": stats.__dict__,
                "detection": detection_status
            })
            
        except Exception as e:
            logger.error(f"Get candidate stats failed: {e}")
            return jsonify({"error": "Stats retrieval failed"}), 500
    
    @bp.route('/maintenance/prune', methods=['POST'])
    @require_token
    def prune_old_candidates():
        """Prune old decided/expired candidates."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            data = request.get_json() or {}
            older_than_days = data.get('older_than_days', 180)
            
            # Validate input
            if not isinstance(older_than_days, int) or older_than_days < 1:
                return jsonify({"error": "older_than_days must be a positive integer"}), 400
            
            count = candidate_service.prune_old_candidates(older_than_days)
            
            return jsonify({
                "success": True,
                "pruned_count": count,
                "older_than_days": older_than_days
            })
            
        except Exception as e:
            logger.error(f"Prune candidates failed: {e}")
            return jsonify({"error": "Prune failed"}), 500
    
    @bp.route('/maintenance/bulk-dismiss-low-confidence', methods=['POST'])
    @require_token
    def bulk_dismiss_low_confidence():
        """Bulk dismiss low-confidence candidates."""
        try:
            if not candidate_service:
                return jsonify({"error": "Candidate service not initialized"}), 503
            
            data = request.get_json() or {}
            max_score = data.get('max_score', 0.3)
            
            # Validate input
            if not isinstance(max_score, (int, float)) or not 0.0 <= max_score <= 1.0:
                return jsonify({"error": "max_score must be between 0.0 and 1.0"}), 400
            
            count = candidate_service.bulk_dismiss_low_confidence(max_score)
            
            return jsonify({
                "success": True,
                "dismissed_count": count,
                "max_score": max_score
            })
            
        except Exception as e:
            logger.error(f"Bulk dismiss failed: {e}")
            return jsonify({"error": "Bulk dismiss failed"}), 500
    
    return bp


def init_candidates_api(service: CandidateService):
    """Initialize candidates API with service instance."""
    global candidate_service
    candidate_service = service
    logger.info("Candidates API initialized")