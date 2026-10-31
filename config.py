import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ecosmart")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_SIZE", str(5 * 1024 * 1024)))
    UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads")))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
    ALLOWED_CATEGORIES = {
        "Mobile Phones", "Laptops", "Batteries", "Chargers",
        "Computer Accessories", "Televisions", "Other Electronic Waste",
    }
    ALLOWED_STATUSES = {"Pending", "In Progress", "Resolved"}
    ALLOWED_COLLECTION_STATUSES = {"Requested", "Scheduled", "Collected", "Cancelled"}


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    UPLOAD_FOLDER = BASE_DIR / "tests" / "uploads"
