from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app


def test_auth_login_success():
    with TestClient(app) as client:
        login_payload = {"email": "admin@soc.local", "password": "Admin@123"}
        res = client.post("/api/v1/auth/login", json=login_payload)
        assert res.status_code == 200, res.text
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"


def test_auth_me_requires_token():
    with TestClient(app) as client:
        res = client.get("/api/v1/auth/me")
        assert res.status_code == 401, res.text


def test_auth_signup_success():
    with TestClient(app) as client:
        payload = {
            "full_name": "SOC Analyst",
            "email": f"analyst-{uuid4().hex[:8]}@soc.local",
            "password": "Analyst@123",
        }
        res = client.post("/api/v1/auth/signup", json=payload)
        assert res.status_code == 200, res.text
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["role"] == "analyst"


def test_reports_generate_success_with_token():
    with TestClient(app) as client:
        # login
        login_payload = {"email": "admin@soc.local", "password": "Admin@123"}
        login_res = client.post("/api/v1/auth/login", json=login_payload)
        assert login_res.status_code == 200, login_res.text
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # create incident first
        attack_payload = {
            "source_ip": "10.10.10.5",
            "destination_ip": "10.10.10.10",
            "attack_type": "SQL Injection",
            "severity": "high",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_message": "select * from users where '1'='1'",
            "status_code": 403,
            "payload": "union select password from users",
        }
        attack_res = client.post(
            "/api/v1/attacks", json=attack_payload, headers=headers
        )
        assert attack_res.status_code == 200, attack_res.text
        incident_id = attack_res.json()["id"]

        # generate report using real incident id
        res = client.post(
            "/api/v1/reports/generate",
            json={"incident_id": incident_id},
            headers=headers,
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["report_name"].endswith(".pdf")
        assert body["report_path"].startswith("reports/")

        attack_lookup = client.get(
            f"/api/v1/attacks/{incident_id}",
            headers=headers,
        )
        assert attack_lookup.status_code == 200, attack_lookup.text
        assert str(attack_lookup.json().get("id")) == str(incident_id)
