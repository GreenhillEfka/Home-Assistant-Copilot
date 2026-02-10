"""Basic integration tests for the tag-system API blueprint."""
from __future__ import annotations

import os
from pathlib import Path
import sys

try:  # pragma: no cover - dev envs without Flask should skip gracefully
    import flask  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - fallback when deps missing
    print("SKIP: Flask not installed; tag-system API tests skipped")
    raise SystemExit(0)

ASSIGNMENTS_FIXTURE = Path(__file__).with_name("test_tag_assignments_store.json")
if ASSIGNMENTS_FIXTURE.exists():
    ASSIGNMENTS_FIXTURE.unlink()
os.environ["COPILOT_TAG_ASSIGNMENTS_PATH"] = str(ASSIGNMENTS_FIXTURE)

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app


def test_list_tags_endpoint():
    client = app.test_client()
    response = client.get("/api/v1/tag-system/tags?lang=en")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["count"] == len(payload["tags"])
    assert "schema_version" in payload
    light_tag = next((t for t in payload["tags"] if t["id"] == "aicp.kind.light"), None)
    assert light_tag is not None
    assert light_tag["display"]["lang"] == "en"
    assert light_tag["ha"]["materialize_as_label"] is True


def test_assignments_crud_flow():
    client = app.test_client()
    response = client.get("/api/v1/tag-system/assignments")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["assignments"] == []
    assert payload["count"] == 0

    empty_post = client.post(
        "/api/v1/tag-system/assignments",
        json={"subject_id": "light.kitchen"},
    )
    assert empty_post.status_code == 400

    create_resp = client.post(
        "/api/v1/tag-system/assignments",
        json={
            "subject_id": "light.kitchen",
            "subject_kind": "entity",
            "tag_id": "aicp.kind.light",
            "materialized": True,
            "meta": {"reason": "test"},
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.get_json()
    assert created["ok"] is True
    assert created["created"] is True
    assert created["assignment"]["subject_id"] == "light.kitchen"

    list_resp = client.get("/api/v1/tag-system/assignments?subject_kind=entity")
    assert list_resp.status_code == 200
    listed = list_resp.get_json()
    assert listed["count"] == 1
    assert listed["assignments"][0]["subject_kind"] == "entity"

    # Second POST should update existing assignment instead of creating a new one
    update_resp = client.post(
        "/api/v1/tag-system/assignments",
        json={
            "subject_id": "light.kitchen",
            "subject_kind": "entity",
            "tag_id": "aicp.kind.light",
            "materialized": False,
        },
    )
    assert update_resp.status_code == 200
    updated_payload = update_resp.get_json()
    assert updated_payload["created"] is False
    assert updated_payload["assignment"]["materialized"] is False

    # Test DELETE single assignment
    assignment_id = updated_payload["assignment"]["assignment_id"]
    delete_resp = client.delete(f"/api/v1/tag-system/assignments/{assignment_id}")
    assert delete_resp.status_code == 200
    deleted = delete_resp.get_json()
    assert deleted["ok"] is True
    assert deleted["deleted"] is True
    assert deleted["assignment_id"] == assignment_id

    # Verify assignment is gone
    list_after_delete = client.get("/api/v1/tag-system/assignments")
    assert list_after_delete.status_code == 200
    assert list_after_delete.get_json()["count"] == 0

    # Test DELETE non-existent assignment
    not_found_resp = client.delete(f"/api/v1/tag-system/assignments/nonexistent")
    assert not_found_resp.status_code == 404
    assert not_found_resp.get_json()["error"] == "assignment_not_found"


def test_assignments_batch_delete():
    client = app.test_client()
    
    # Create test assignments
    assignments = []
    for i in range(3):
        create_resp = client.post(
            "/api/v1/tag-system/assignments",
            json={
                "subject_id": f"light.test_{i}",
                "subject_kind": "entity", 
                "tag_id": "aicp.kind.light",
                "materialized": True,
            },
        )
        assert create_resp.status_code == 201
        assignments.append(create_resp.get_json()["assignment"]["assignment_id"])

    # Test batch delete
    batch_delete_resp = client.delete(
        "/api/v1/tag-system/assignments/batch",
        json={"assignment_ids": assignments[:2]}  # Delete first 2
    )
    assert batch_delete_resp.status_code == 200
    batch_result = batch_delete_resp.get_json()
    assert batch_result["ok"] is True
    assert batch_result["requested"] == 2
    assert batch_result["deleted"] == 2
    assert batch_result["not_found"] == 0

    # Verify only 1 assignment remains
    list_resp = client.get("/api/v1/tag-system/assignments")
    assert list_resp.status_code == 200
    assert list_resp.get_json()["count"] == 1

    # Test batch delete with mix of existing and non-existing
    batch_mixed_resp = client.delete(
        "/api/v1/tag-system/assignments/batch",
        json={"assignment_ids": [assignments[2], "nonexistent1", "nonexistent2"]}
    )
    assert batch_mixed_resp.status_code == 200
    mixed_result = batch_mixed_resp.get_json()
    assert mixed_result["requested"] == 3
    assert mixed_result["deleted"] == 1  # Only the existing one
    assert mixed_result["not_found"] == 2

    # Test invalid payload
    invalid_resp = client.delete(
        "/api/v1/tag-system/assignments/batch",
        json={"invalid": "payload"}
    )
    assert invalid_resp.status_code == 400
    assert "assignment_ids" in invalid_resp.get_json()["detail"]
