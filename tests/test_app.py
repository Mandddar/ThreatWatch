import pytest
from app import app, analyze_url


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_safe_url():
    result = analyze_url("https://example.com")
    assert result["risk_score"] == 0
    assert result["risk_level"] == "LOW"


def test_http_url():
    result = analyze_url("http://example.com")
    assert result["risk_score"] == 20
    assert result["risk_level"] == "LOW"


def test_high_risk_url():
    result = analyze_url(
        "http://192.168.1.10/login/verify/account"
    )
    assert result["risk_score"] == 75
    assert result["risk_level"] == "HIGH"


def test_invalid_scan_request(client):
    response = client.post("/api/scan", json={})
    assert response.status_code == 400


def test_scan_api(client):
    response = client.post(
        "/api/scan",
        json={"url": "https://example.com"}
    )
    assert response.status_code == 200
    assert response.json["risk_level"] == "LOW"


def test_invalid_scheme(client):
    response = client.post(
        "/api/scan",
        json={"url": "ftp://example.com"}
    )
    assert response.status_code == 400
