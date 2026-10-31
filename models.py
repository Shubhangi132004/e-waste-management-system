from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user", index=True)

    reports = db.relationship("Report", back_populates="user", cascade="all, delete-orphan")
    collection_requests = db.relationship("CollectionRequest", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Report(TimestampMixin, db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    issue_type = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Numeric(10, 7), nullable=True)
    longitude = db.Column(db.Numeric(10, 7), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending", index=True)

    user = db.relationship("User", back_populates="reports")
    collection_requests = db.relationship("CollectionRequest", back_populates="report", cascade="all, delete-orphan")


class CollectionRequest(TimestampMixin, db.Model):
    __tablename__ = "collection_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = db.Column(db.Integer, db.ForeignKey("reports.id", ondelete="SET NULL"), nullable=True, index=True)
    category = db.Column(db.String(80), nullable=False)
    collection_address = db.Column(db.String(500), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    collection_status = db.Column(db.String(20), nullable=False, default="Requested", index=True)
    notes = db.Column(db.Text, nullable=True)

    user = db.relationship("User", back_populates="collection_requests")
    report = db.relationship("Report", back_populates="collection_requests")
