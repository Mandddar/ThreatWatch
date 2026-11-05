
from flask import Flask, render_template, request, jsonify
from urllib.parse import urlparse
from datetime import datetime
import sqlite3
import re

app = Flask(__name__)

import os

DATABASE = os.environ.get("DATABASE", "threatwatch.db")

SUSPICIOUS_KEYWORDS = [
    "login", "verify", "secure", "account",
    "update", "banking", "password", "wallet"
]

SHORTENED_DOMAINS = [
    "bit.ly", "tinyurl.com", "t.co",
    "is.gd", "cutt.ly", "shorturl.at"
]


def initialize_database():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            scanned_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def analyze_url(url):
    score = 0
    reasons = []

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    lower_url = url.lower()

    if parsed.scheme != "https":
        score += 20
        reasons.append("URL does not use HTTPS")

    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
        score += 25
        reasons.append("URL uses an IP address instead of a domain")

    if hostname in SHORTENED_DOMAINS:
        score += 20
        reasons.append("URL uses a shortened domain")

    if hostname.startswith("xn--") or ".xn--" in hostname:
        score += 20
        reasons.append("Domain contains an internationalized hostname")

    if hostname.count("-") >= 3:
        score += 10
        reasons.append("Domain contains multiple hyphens")

    if hostname.count(".") >= 4:
        score += 10
        reasons.append("Unusually deep subdomain structure")

    if "@" in url:
        score += 20
        reasons.append("URL contains an @ symbol")

    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in lower_url:
            score += 10
            reasons.append(f"Suspicious keyword detected: {keyword}")

    score = min(score, 100)

    if score >= 60:
        level = "HIGH"
    elif score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "url": url,
        "risk_score": score,
        "risk_level": level,
        "reasons": reasons
    }


def save_scan(result):
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        """INSERT INTO scans
        (url, risk_score, risk_level, scanned_at)
        VALUES (?, ?, ?, ?)""",
        (
            result["url"],
            result["risk_score"],
            result["risk_level"],
            datetime.now().isoformat(timespec="seconds")
        )
    )
    conn.commit()
    conn.close()


@app.route("/")
def dashboard():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    scans = conn.execute(
        "SELECT * FROM scans ORDER BY id DESC LIMIT 10"
    ).fetchall()

    stats = conn.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high,
            SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium,
            SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) AS low
        FROM scans
    """).fetchone()

    conn.close()

    return render_template(
        "index.html",
        scans=scans,
        stats=stats
    )


@app.route("/api/scan", methods=["POST"])
def scan():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url or len(url) > 2048:
        return jsonify({"error": "Provide a URL of up to 2048 characters"}), 400

    if any(ord(char) < 32 for char in url):
        return jsonify({"error": "URL contains invalid characters"}), 400

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return jsonify({"error": "Enter a valid HTTP or HTTPS URL"}), 400

    try:
        result = analyze_url(url)
        save_scan(result)
        return jsonify(result)
    except Exception:
        app.logger.exception("URL analysis failed")
        return jsonify({"error": "Unable to analyze URL"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "application": "ThreatWatch"})


@app.route("/api/history")
def history():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    scans = conn.execute(
        "SELECT * FROM scans ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()

    return jsonify([dict(row) for row in scans])


initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

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
    assert result["risk_score"] == 85
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
