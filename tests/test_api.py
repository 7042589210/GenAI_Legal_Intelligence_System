from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Tata Legal AI System API is running" in response.json()["status"]

def test_analyze_contract_unsupported_file():
    files = {"file": ("test.txt", b"dummy content", "text/plain")}
    response = client.post("/api/analyze-contract", files=files)
    assert response.status_code == 400
    assert "Only PDF and DOCX files are supported." in response.json()["detail"]
