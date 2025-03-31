import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from db.sql_lite import DB
from model.lead_model import Lead

client = TestClient(app)

# Setup: ensure a fresh DB for each test session
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    db = DB()
    db.init_db()

# Test submitting a lead
def test_create_lead():
    resume_content = b"Test Resume Content"
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(resume_content)
        temp_file_path = temp_file.name

    with open(temp_file_path, "rb") as resume:
        response = client.post(
            "/lead",
            files={"resume": ("resume.txt", resume, "text/plain")},
            data={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com"
            }
        )

    os.unlink(temp_file_path)
    assert response.status_code == 200
    assert response.json()["message"] == "Lead submitted successfully"

# Test getting leads (requires auth)
def test_get_leads():
    response = client.get("/leads", auth=("attorney", "password123"))
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Test marking a lead as REACHED_OUT (requires auth)
def test_mark_as_reached_out():
    leads_response = client.get("/leads", auth=("attorney", "password123"))
    assert leads_response.status_code == 200
    leads = leads_response.json()
    assert len(leads) > 0

    lead_id = leads[0]["id"]
    response = client.put(f"/lead/{lead_id}/reach_out", auth=("attorney", "password123"))
    assert response.status_code == 200
    assert response.json()["message"] == "Lead marked as REACHED_OUT"