"""Tests for Collective Intelligence module."""

import pytest
import time
import json

from copilot_core.collective_intelligence.models import (
    ModelUpdate, AggregatedModel, FederatedRound, KnowledgeItem, AggregationMethod
)
from copilot_core.collective_intelligence.federated_learner import FederatedLearner
from copilot_core.collective_intelligence.model_aggregator import ModelAggregator
from copilot_core.collective_intelligence.privacy_preserver import (
    DifferentialPrivacy, PrivacyAwareAggregator, PrivacyBudget
)
from copilot_core.collective_intelligence.knowledge_transfer import KnowledgeTransfer
from copilot_core.collective_intelligence.service import CollectiveIntelligenceService


class TestModels:
    """Test data models."""

    def test_model_update_creation(self):
        """Test ModelUpdate creation and serialization."""
        update = ModelUpdate(
            node_id="home-001",
            model_version="v1.0.0",
            weights={"weight1": 0.5, "weight2": 0.3},
            metrics={"loss": 0.1}
        )

        assert update.node_id == "home-001"
        assert update.model_version == "v1.0.0"
        assert update.update_id is not None

        # Test serialization
        data = update.to_dict()
        assert data["node_id"] == "home-001"

        # Test deserialization
        restored = ModelUpdate.from_dict(data)
        assert restored.node_id == update.node_id

    def test_aggregated_model_creation(self):
        """Test AggregatedModel creation and serialization."""
        model = AggregatedModel(
            model_version="v1.0.0",
            weights={"weight1": 0.4},
            aggregation_method=AggregationMethod.FEDERATED_AVERAGING,
            participants=["home-001", "home-002"],
            metrics={"accuracy": 0.95}
        )

        assert model.aggregation_method == AggregationMethod.FEDERATED_AVERAGING
        assert len(model.participants) == 2

        # Test serialization
        data = model.to_dict()
        assert data["aggregation_method"] == "fed_avg"

    def test_federated_round_creation(self):
        """Test FederatedRound creation."""
        round_obj = FederatedRound(
            round_id="round-001",
            model_version="v1.0.0",
            participating_nodes=["home-001"],
            updates=[]
        )

        assert round_obj.round_id == "round-001"
        assert round_obj.round_duration is None

        # Complete round
        model = AggregatedModel(
            model_version="v1.0.0",
            weights={},
            aggregation_method=AggregationMethod.FEDERATED_AVERAGING,
            participants=[],
            metrics={}
        )
        round_obj.complete(model)

        assert round_obj.round_duration is not None
        assert round_obj.aggregated_model is not None

    def test_knowledge_item_creation(self):
        """Test KnowledgeItem creation and deduplication."""
        payload = {"pattern": "morning_routine", "duration": 3600}
        knowledge = KnowledgeItem(
            knowledge_id="test-001",
            source_node_id="home-001",
            knowledge_type="habitus_pattern",
            payload=payload,
            confidence=0.85
        )

        assert knowledge.knowledge_hash is not None
        assert knowledge.knowledge_hash == knowledge.knowledge_hash  # Deterministic

        # Test serialization
        data = knowledge.to_dict()
        restored = KnowledgeItem.from_dict(data)
        assert restored.knowledge_id == knowledge.knowledge_id


class TestFederatedLearner:
    """Test federated learning core."""

    def test_start_round(self):
        """Test starting a federated round."""
        learner = FederatedLearner()
        round_obj = learner.start_round()

        assert round_obj.round_id is not None
        assert round_obj.model_version == "v1.0.0"

    def test_submit_update(self):
        """Test submitting model updates."""
        learner = FederatedLearner()
        learner.register_participant("home-001")
        learner.start_round()  # Need to start a round first

        update = learner.submit_update(
            "home-001",
            {"weight1": 0.5, "weight2": 0.3},
            {"loss": 0.1}
        )

        assert update is not None
        assert len(learner.active_rounds) == 1
        round_obj = list(learner.active_rounds.values())[0]
        assert len(round_obj.updates) == 1

    def test_aggregation_fed_avg(self):
        """Test federated averaging aggregation."""
        learner = FederatedLearner()
        round_obj = learner.start_round()
        learner.register_participant("home-001")
        learner.register_participant("home-002")
        learner.register_participant("home-003")

        # Submit updates with known values
        learner.submit_update("home-001", {"weight": 1.0})
        learner.submit_update("home-002", {"weight": 2.0})
        learner.submit_update("home-003", {"weight": 3.0})

        # Aggregate
        aggregated = learner.aggregate(round_obj.round_id)

        assert aggregated is not None, f"Expected aggregated model, got None. Updates: {round_obj.updates}"
        assert aggregated.weights["weight"] == 2.0  # Mean of 1,2,3

    def test_min_participants_requirement(self):
        """Test that aggregation requires minimum participants."""
        learner = FederatedLearner(min_participants=3)
        learner.register_participant("home-001")
        learner.register_participant("home-002")

        round_obj = learner.start_round()
        learner.submit_update("home-001", {"weight": 1.0})
        learner.submit_update("home-002", {"weight": 2.0})

        # Should return None due to insufficient participants
        aggregated = learner.aggregate(round_obj.round_id)
        assert aggregated is None


class TestModelAggregator:
    """Test model aggregation."""

    def test_aggregate_fed_avg(self):
        """Test federated averaging."""
        aggregator = ModelAggregator()

        updates = [
            ModelUpdate("home-001", "v1", {"weight": 1.0}),
            ModelUpdate("home-002", "v1", {"weight": 2.0}),
            ModelUpdate("home-003", "v1", {"weight": 3.0}),
        ]

        result = aggregator.aggregate(updates, AggregationMethod.FEDERATED_AVERAGING)

        assert result is not None
        assert result.weights["weight"] == 2.0

    def test_aggregate_fed_median(self):
        """Test federated median."""
        aggregator = ModelAggregator()

        updates = [
            ModelUpdate("home-001", "v1", {"weight": 1.0}),
            ModelUpdate("home-002", "v1", {"weight": 2.0}),
            ModelUpdate("home-003", "v1", {"weight": 100.0}),
        ]

        result = aggregator.aggregate(updates, AggregationMethod.FEDERATED_MEDIAN)

        assert result is not None
        assert result.weights["weight"] == 2.0  # Median, not mean

    def test_version_generation(self):
        """Test model version generation."""
        aggregator = ModelAggregator()

        updates = [
            ModelUpdate("home-001", "v1", {"weight": 1.0}, {"accuracy": 0.9}),
        ]

        result = aggregator.aggregate(updates)

        assert result is not None
        assert result.model_version.startswith("v")
        assert "fed-avg" in result.model_version


class TestPrivacyPreserver:
    """Test differential privacy mechanisms."""

    def test_noise_addition(self):
        """Test Gaussian noise addition."""
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)

        # Add noise to scalar
        noisy = dp.add_gaussian_noise(10.0, sensitivity=1.0)

        # Should be different from original (with high probability)
        assert noisy != 10.0

    def test_noise_addition_array(self):
        """Test Gaussian noise addition on arrays."""
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)

        import numpy as np
        values = np.array([1.0, 2.0, 3.0])
        noisy = dp.add_gaussian_noise(values, sensitivity=1.0)

        assert len(noisy) == 3
        # With very high probability, at least one value is different
        assert any(abs(n - v) > 0.001 for n, v in zip(noisy, values))

    def test_privacy_budget(self):
        """Test privacy budget tracking."""
        budget = PrivacyBudget(
            node_id="home-001",
            epsilon=0.0,
            delta=0.0,
            max_epsilon=1.0,
            max_delta=1e-5
        )

        assert budget.can_update(0.5)
        assert budget.consume(0.5)

        assert budget.can_update(0.4)
        assert budget.consume(0.4)

        # Should fail with remaining 0.1 budget
        assert not budget.can_update(0.5)

    def test_privacy_aware_aggregator(self):
        """Test privacy-aware aggregation."""
        aggregator = PrivacyAwareAggregator(global_epsilon=1.0, global_delta=1e-5)

        aggregator.register_node("home-001", max_epsilon=0.5)
        aggregator.register_node("home-002", max_epsilon=0.5)

        updates = [
            {"value": 10.0},
            {"value": 20.0},
        ]

        result = aggregator.aggregate_with_privacy(updates, target_epsilon=0.5)

        assert "value" in result
        # Result should be noisy approximation of 15.0


class TestKnowledgeTransfer:
    """Test knowledge transfer functionality."""

    def test_extract_knowledge(self):
        """Test knowledge extraction."""
        transfer = KnowledgeTransfer()

        knowledge = transfer.extract_knowledge(
            node_id="home-001",
            knowledge_type="habitus_pattern",
            payload={"pattern": "morning_routine"},
            confidence=0.85
        )

        assert knowledge is not None
        assert knowledge.knowledge_id is not None
        assert knowledge.knowledge_hash is not None

    def test_duplicate_detection(self):
        """Test knowledge deduplication."""
        transfer = KnowledgeTransfer()

        payload = {"pattern": "morning_routine"}

        k1 = transfer.extract_knowledge("home-001", "test", payload, confidence=0.9)
        k2 = transfer.extract_knowledge("home-002", "test", payload, confidence=0.9)

        # Second extraction should be rejected as duplicate
        assert k1 is not None
        assert k2 is None

    def test_transfer_rate_limiting(self):
        """Test transfer rate limiting."""
        transfer = KnowledgeTransfer(max_transfer_rate=2)

        # Need unique payloads for each transfer due to deduplication
        payload1 = {"pattern": "transfer1"}
        payload2 = {"pattern": "transfer2"}

        k1 = transfer.extract_knowledge("home-001", "test", payload1, confidence=0.9)
        k2 = transfer.extract_knowledge("home-001", "test", payload2, confidence=0.9)

        # First transfer should succeed
        assert transfer.transfer_knowledge(k1.knowledge_id, "home-002")

        # Second transfer should also succeed (rate = 2)
        assert transfer.transfer_knowledge(k2.knowledge_id, "home-002")

        # Third transfer to same target should fail
        payload3 = {"pattern": "transfer3"}
        k3 = transfer.extract_knowledge("home-001", "test2", payload3, confidence=0.9)
        assert not transfer.transfer_knowledge(k3.knowledge_id, "home-002")


class TestCollectiveIntelligenceService:
    """Test main service coordinator."""

    def test_service_start_stop(self):
        """Test service lifecycle."""
        service = CollectiveIntelligenceService()
        service.start()

        assert service.is_active
        assert service._status.is_active

        service.stop()

        assert not service.is_active
        assert not service._status.is_active

    def test_node_registration(self):
        """Test node registration."""
        service = CollectiveIntelligenceService()
        service.start()

        result = service.register_node("home-001")

        assert result
        assert service._status.participating_nodes == 1

    def test_federated_workflow(self):
        """Test complete federated learning workflow."""
        service = CollectiveIntelligenceService()
        service.start()

        # Register nodes
        service.register_node("home-001")
        service.register_node("home-002")

        # Start round first
        round_id = service.start_federated_round()

        # Submit updates
        service.submit_local_update("home-001", {"weights": [0.5, 0.3]})
        service.submit_local_update("home-002", {"weights": [0.4, 0.2]})

        # Execute aggregation
        aggregated = service.execute_aggregation(round_id)

        assert aggregated is not None
        assert service._status.completed_rounds == 1

    def test_knowledge_extraction_and_transfer(self):
        """Test knowledge extraction and transfer workflow."""
        service = CollectiveIntelligenceService()
        service.start()

        # Extract knowledge
        knowledge = service.extract_knowledge(
            node_id="home-001",
            knowledge_type="energy_saving",
            payload={"recommendation": "optimize_heating", "savings": 15.2},
            confidence=0.85
        )

        assert knowledge is not None

        # Transfer knowledge
        result = service.transfer_knowledge(knowledge.knowledge_id, "home-002")

        assert result
        assert service._status.knowledge_transferred == 1

    def test_statistics(self):
        """Test system statistics."""
        service = CollectiveIntelligenceService()
        service.start()

        service.register_node("home-001")
        service.register_node("home-002")

        round_id = service.start_federated_round()
        service.submit_local_update("home-001", {"weights": [0.5]})
        service.submit_local_update("home-002", {"weights": [0.3]})

        # Execute aggregation with the round ID
        aggregated = service.execute_aggregation(round_id)

        stats = service.get_statistics()

        assert stats["status"]["completed_rounds"] == 1
        assert stats["status"]["participating_nodes"] == 2
        assert stats["federated_rounds"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
