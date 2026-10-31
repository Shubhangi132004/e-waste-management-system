import io
from datetime import date, timedelta

import pytest
from PIL import Image

from app import create_app
from config import TestConfig
from models import User, db


@pytest.fixture()
def app(tmp_path):
    class LocalTestConfig(TestConfig):
        UPLOAD_FOLDER = tmp_path
        SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"
    app = create_app(LocalTestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf(client):
    return client.get("/api/csrf-token").get_json()["csrf_token"]


def register(client, email="user@example.com"):
    token = csrf(client)
    return client.post("/api/auth/register", json={"full_name": "Test User", "email": email, "password": "password123"}, headers={"X-CSRFToken": token})


def login(client, email="user@example.com", password="password123"):
    token = csrf(client)
    return client.post("/api/auth/login", json={"email": email, "password": password}, headers={"X-CSRFToken": token})


def test_application_startup_and_registration(client):
    response = register(client)
    assert response.status_code == 201
    assert response.get_json()["user"]["role"] == "user"


def test_duplicate_registration_and_login(client):
    register(client)
    duplicate = register(client)
    assert duplicate.status_code == 409
    client.post("/api/auth/logout", headers={"X-CSRFToken": csrf(client)})
    assert login(client).status_code == 200
    assert login(client, password="wrong").status_code == 401


def test_report_validation_and_creation(client):
    response = client.post("/api/reports", data={"name": "", "location": "", "issue_type": "Unknown"}, headers={"X-CSRFToken": csrf(client)})
    assert response.status_code == 400
    invalid = client.post("/api/reports", data={"name": "Reporter", "location": "Pune", "issue_type": "Laptops", "image": (io.BytesIO(b"fake image"), "device.png")}, content_type="multipart/form-data", headers={"X-CSRFToken": csrf(client)})
    assert invalid.status_code == 400
    valid_image = io.BytesIO()
    Image.new("RGB", (2, 2), color="green").save(valid_image, format="PNG")
    valid_image.seek(0)
    response = client.post("/api/reports", data={"name": "Reporter", "location": "Pune", "issue_type": "Laptops", "description": "Old device", "image": (valid_image, "device.png")}, content_type="multipart/form-data", headers={"X-CSRFToken": csrf(client)})
    assert response.status_code == 201
    assert response.get_json()["issue_id"] == 1


def test_report_retrieval_and_stats(client):
    register(client)
    client.post("/api/reports", data={"name": "Reporter", "location": "Pune", "issue_type": "Batteries"}, headers={"X-CSRFToken": csrf(client)})
    assert len(client.get("/api/reports").get_json()["reports"]) == 1
    stats_response = client.get("/api/stats")
    stats = stats_response.get_json()
    assert stats["total_reported"] == 1
    assert stats["pending"] == 1
    assert len(stats["recent_reports"]) == 1
    assert "Reporter" not in stats_response.get_data(as_text=True)
    assert "Pune" not in stats_response.get_data(as_text=True)


def test_homepage_and_frontend_assets_are_served(client):
    homepage = client.get("/")
    assert homepage.status_code == 200
    assert b"aiSuggestBtn" in homepage.data
    assert client.get("/style.css").status_code == 200
    assert client.get("/script.js").status_code == 200


def test_admin_access_and_report_management(client, app):
    assert client.get("/api/admin/reports").status_code == 401
    with app.app_context():
        admin = User(full_name="Admin", email="admin@example.com", role="admin")
        admin.set_password("adminpass123")
        db.session.add(admin)
        db.session.commit()
    assert login(client, "admin@example.com", "adminpass123").status_code == 200
    created = client.post("/api/reports", data={"name": "Reporter", "location": "Pune", "issue_type": "Chargers"}, headers={"X-CSRFToken": csrf(client)})
    report_id = created.get_json()["issue_id"]
    updated = client.put(f"/api/admin/reports/{report_id}", json={"status": "Resolved"}, headers={"X-CSRFToken": csrf(client)})
    assert updated.status_code == 200
    assert client.delete(f"/api/admin/reports/{report_id}", headers={"X-CSRFToken": csrf(client)}).status_code == 200


def test_collection_request(client):
    register(client)
    payload = {"category": "Mobile Phones", "collection_address": "Community center", "preferred_date": (date.today() + timedelta(days=2)).isoformat(), "notes": "Call first"}
    response = client.post("/api/collections", json=payload, headers={"X-CSRFToken": csrf(client)})
    assert response.status_code == 201
    assert len(client.get("/api/collections").get_json()["collection_requests"]) == 1


def test_ai_category_suggestion_requires_csrf_and_returns_local_model_result(client):
    payload = {"text": "My smartphone has a cracked screen and no longer turns on."}
    denied = client.post("/api/ai/suggest-category", json=payload)
    assert denied.status_code == 400
    response = client.post("/api/ai/suggest-category", json=payload, headers={"X-CSRFToken": csrf(client)})
    assert response.status_code == 200
    result = response.get_json()
    assert result["suggested_category"] == "Mobile Phones"
    assert result["model"] == "ewaste-tfidf-logreg-v1"
    assert len(result["alternatives"]) == 3


def test_ai_model_metadata_and_database_health(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.get_json()["database"] == "connected"
    model = client.get("/api/ai/model")
    assert model.status_code == 200
    metadata = model.get_json()
    assert metadata["library"] == "scikit-learn"
    assert metadata["training_examples"] >= 80
