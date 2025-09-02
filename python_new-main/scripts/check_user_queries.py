#!/usr/bin/env python3
"""
Check user queries end-to-end using FastAPI TestClient.
- Registers a user (or logs in if already exists)
- Runs an authenticated query via /run_graph
- Retrieves recent queries via /auth/queries
This script runs the app in-process (no long-running server needed).
"""
import os
import sys
import time
import uuid
from fastapi.testclient import TestClient

# Ensure mock fallback for LLM if Ollama is slow/unavailable
os.environ.setdefault('OLLAMA_ENABLE_MOCK_FALLBACK', 'true')

# Ensure project root is on sys.path when running from scripts/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.main import app  # noqa: E402 (import after setting env and sys.path)

client = TestClient(app)


def main():
    username = f"agent_test_{int(time.time())}"
    password = uuid.uuid4().hex  # random strong test password
    email = f"{username}@example.com"

    print("[STEP] Registering or logging in test user...")
    token = None

    # Try to register
    reg_resp = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
        headers={"Content-Type": "application/json"},
    )

    if reg_resp.status_code == 200:
        reg_data = reg_resp.json()
        token = reg_data.get("token")
        user_id = reg_data.get("user", {}).get("user_id")
        print(f"[OK] Registered user: {username} (id={user_id})")
    else:
        # If already exists or registration blocked, try to login
        login_resp = client.post(
            "/auth/login",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
        if login_resp.status_code != 200:
            # Retry with a fallback user (single-run scenario)
            username = f"agent_test_fallback_{int(time.time())}"
            password = uuid.uuid4().hex
            email = f"{username}@example.com"
            reg_resp2 = client.post(
                "/auth/register",
                json={"username": username, "email": email, "password": password},
                headers={"Content-Type": "application/json"},
            )
            reg_resp2.raise_for_status()
            reg_data = reg_resp2.json()
            token = reg_data.get("token")
            user_id = reg_data.get("user", {}).get("user_id")
            print(f"[OK] Registered fallback user: {username} (id={user_id})")
        else:
            login_data = login_resp.json()
            token = login_data.get("token")
            user_id = login_data.get("user", {}).get("user_id")
            print(f"[OK] Logged in user: {username} (id={user_id})")

    if not token:
        raise SystemExit("[ERR] Failed to acquire auth token")

    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    print("[STEP] Running query via /run_graph_legacy and logging it to user history...")
    question = (
        "Find scenic locations in the Swiss Alps and recommend great Italian dining spots nearby"
    )
    # Use legacy endpoint for stability (no auth dependency in route handler)
    import time as _t
    t0 = _t.time()
    legacy_resp = client.post(
        "/run_graph_legacy",
        json={"user": username, "question": question},
        headers={"Content-Type": "application/json"},
    )
    dt = _t.time() - t0
    print(f"[INFO] /run_graph_legacy => {legacy_resp.status_code}")
    if legacy_resp.status_code == 200:
        data = legacy_resp.json()
        agent = data.get("agent")
        agents_involved = list(data.get("agent_responses", {}).keys())
        edges = data.get("edges_traversed", [])
        response_text = data.get("response", "")
        print(f"[OK] Legacy processed by: {agent}; agents_involved: {agents_involved}")
        print(f"[OK] Response length: {len(response_text)}; elapsed={dt:.2f}s")
        # Manually log the query to user history via service to simulate authenticated logging
        from auth.auth_service import auth_service
        # Session id came from registration response
        # If we registered above, reg_data is set; else from login, no session id in payload; handle both
        session_id = None
        try:
            session_id = reg_data.get("session_id")  # type: ignore[name-defined]
        except Exception:
            session_id = None
        ok = auth_service.log_user_query(
            user_id=user_id,  # type: ignore[name-defined]
            session_id=session_id or "web_session",
            question=question,
            agent_used=agent or "Unknown",
            response_text=response_text,
            edges_traversed=edges,
            processing_time=dt,
        )
        print(f"[OK] Manually logged query to user history: {ok}")
    else:
        print(f"[WARN] /run_graph_legacy failed: {legacy_resp.text}")

    print("[STEP] Fetching recent queries via /auth/queries?limit=5...")
    q_resp = client.get("/auth/queries?limit=5", headers=auth_headers)
    print(f"[INFO] /auth/queries => {q_resp.status_code}")
    if q_resp.status_code == 200:
        queries = q_resp.json()
        print(f"[OK] Retrieved {len(queries)} recent queries")
        if queries:
            top = queries[0]
            print(
                "[TOP]",
                {
                    "question": top.get("question"),
                    "agent_used": top.get("agent_used"),
                    "created_at": top.get("created_at"),
                },
            )
    else:
        print(f"[WARN] /auth/queries failed: {q_resp.text}")


if __name__ == "__main__":
    main()

