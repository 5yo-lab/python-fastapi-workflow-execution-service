import pytest
from httpx import AsyncClient

WORKFLOW_PAYLOAD = {"customerId": "customer-1", "amount": 100}
INVALID_PAYLOAD = {"customerId": "customer-1", "amount": 0}


async def create_workflow(client: AsyncClient, payload: dict = WORKFLOW_PAYLOAD) -> dict:
    response = await client.post(
        "/workflows",
        json={"reference": "WF-TEST", "payload": payload},
    )
    assert response.status_code == 201
    return response.json()


async def apply_transition(
    client: AsyncClient,
    workflow_id: str,
    action: str,
    expected_version: int,
) -> dict:
    response = await client.post(
        f"/workflows/{workflow_id}/transitions",
        json={"action": action, "expectedVersion": expected_version},
    )
    return response


async def get_pending_action_id(client: AsyncClient) -> str:
    response = await client.get("/actions/pending")
    assert response.status_code == 200
    actions = response.json()
    assert len(actions) == 1
    return actions[0]["id"]


async def claim_and_submit_result(
    client: AsyncClient,
    action_id: str,
    *,
    success: bool,
    result: dict | None = None,
    error: str | None = None,
) -> dict:
    claim_response = await client.post(f"/actions/{action_id}/claim")
    assert claim_response.status_code == 200

    result_response = await client.post(
        f"/actions/{action_id}/result",
        json={"success": success, "result": result, "error": error},
    )
    assert result_response.status_code == 200
    return result_response.json()


async def test_valid_transition(client: AsyncClient):
    workflow = await create_workflow(client)

    response = await apply_transition(
        client, workflow["id"], "START_VALIDATION", workflow["version"]
    )
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "VALIDATING"
    assert body["version"] == workflow["version"] + 1

    history_response = await client.get(f"/workflows/{workflow['id']}/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["fromState"] == "CREATED"
    assert history[0]["toState"] == "VALIDATING"
    assert history[0]["action"] == "START_VALIDATION"


async def test_invalid_transition(client: AsyncClient):
    workflow = await create_workflow(client)

    response = await apply_transition(
        client, workflow["id"], "START_PROCESSING", workflow["version"]
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "INVALID_TRANSITION"
    assert "START_PROCESSING" in body["message"]


async def test_stale_version(client: AsyncClient):
    workflow = await create_workflow(client)

    response = await apply_transition(
        client, workflow["id"], "START_VALIDATION", expected_version=999
    )
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_VERSION"


async def test_worker_result_success(client: AsyncClient):
    workflow = await create_workflow(client)
    await apply_transition(
        client, workflow["id"], "START_VALIDATION", workflow["version"]
    )

    action_id = await get_pending_action_id(client)
    await claim_and_submit_result(
        client, action_id, success=True, result={"validated": True}
    )

    workflow_response = await client.get(f"/workflows/{workflow['id']}")
    assert workflow_response.status_code == 200
    body = workflow_response.json()
    assert body["state"] == "APPROVED"
    assert body["version"] == 3


async def test_worker_result_failure(client: AsyncClient):
    workflow = await create_workflow(client, payload=INVALID_PAYLOAD)
    await apply_transition(
        client, workflow["id"], "START_VALIDATION", workflow["version"]
    )

    action_id = await get_pending_action_id(client)
    for _ in range(3):
        await claim_and_submit_result(
            client,
            action_id,
            success=False,
            error="Amount must be positive",
        )

    workflow_response = await client.get(f"/workflows/{workflow['id']}")
    assert workflow_response.status_code == 200
    body = workflow_response.json()
    assert body["state"] == "VALIDATION_FAILED"
    assert body["version"] == 3


async def test_idempotency(client: AsyncClient):
    workflow = await create_workflow(client)
    await apply_transition(
        client, workflow["id"], "START_VALIDATION", workflow["version"]
    )

    action_id = await get_pending_action_id(client)
    await claim_and_submit_result(
        client, action_id, success=True, result={"validated": True}
    )

    duplicate_response = await client.post(
        f"/actions/{action_id}/result",
        json={"success": True, "result": {"validated": True}},
    )
    assert duplicate_response.status_code == 200

    history_response = await client.get(f"/workflows/{workflow['id']}/history")
    assert history_response.status_code == 200
    history = history_response.json()
    approve_entries = [entry for entry in history if entry["action"] == "APPROVE"]
    assert len(approve_entries) == 1

    workflow_response = await client.get(f"/workflows/{workflow['id']}")
    assert workflow_response.json()["state"] == "APPROVED"
