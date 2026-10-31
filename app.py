import os
import secrets
from datetime import date
from functools import wraps
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, redirect, request, send_from_directory, session, url_for
from flask_cors import CORS
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_migrate import Migrate
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from ai.category_classifier import get_classifier
from config import Config
from models import CollectionRequest, Report, User, db


def create_app(config_object=Config):
    app = Flask(__name__, static_folder=".", static_url_path="")
    app.config.from_object(config_object)
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager(app)
    login_manager.login_view = "login_page"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify(error="Authentication is required."), 401
        return redirect(url_for("login_page", next=request.path))

    allowed_origins = os.getenv("CORS_ORIGINS", "").strip()
    if allowed_origins:
        CORS(app, origins=[origin.strip() for origin in allowed_origins.split(",") if origin.strip()], supports_credentials=True)

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return session["csrf_token"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    def csrf_protected(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
            if not token or not secrets.compare_digest(token, session.get("csrf_token", "")):
                return jsonify(error="Invalid or missing CSRF token."), 400
            return view(*args, **kwargs)
        return wrapped

    def admin_required(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role != "admin":
                return jsonify(error="Administrator access is required."), 403
            return view(*args, **kwargs)
        return wrapped

    def json_error(message, status=400):
        return jsonify(error=message), status

    def serialize_report(report):
        return {
            "id": report.id,
            "user_id": report.user_id,
            "name": report.name,
            "location": report.location,
            "issue_type": report.issue_type,
            "description": report.description or "",
            "image": report.image_filename,
            "image_url": url_for("uploaded_file", filename=report.image_filename) if report.image_filename else None,
            "latitude": float(report.latitude) if report.latitude is not None else None,
            "longitude": float(report.longitude) if report.longitude is not None else None,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
        }

    def serialize_collection(item):
        return {
            "id": item.id,
            "report_id": item.report_id,
            "category": item.category,
            "collection_address": item.collection_address,
            "preferred_date": item.preferred_date.isoformat(),
            "collection_status": item.collection_status,
            "notes": item.notes or "",
            "created_at": item.created_at.isoformat(),
        }

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        return json_error("The uploaded file is too large. Maximum size is 5 MB.", 413)

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return json_error("An unexpected server error occurred.", 500)

    @app.route("/")
    def home():
        return send_from_directory(".", "index.html")

    @app.route("/admin")
    def admin_page():
        if not current_user.is_authenticated:
            return redirect(url_for("login_page", next="/admin"))
        if current_user.role != "admin":
            return redirect(url_for("home"))
        return send_from_directory(".", "admin.html")

    @app.route("/login")
    def login_page():
        return send_from_directory(".", "login.html")

    @app.route("/register")
    def register_page():
        return send_from_directory(".", "register.html")

    @app.route("/<path:filename>")
    def serve_static(filename):
        return send_from_directory(".", filename)

    @app.route("/api/csrf-token")
    def csrf_endpoint():
        return jsonify(csrf_token=csrf_token())

    @app.get("/api/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            app.logger.exception("Database health check failed")
            return jsonify(status="error", database="unavailable"), 503
        return jsonify(status="ok", database="connected")

    @app.post("/api/auth/register")
    @csrf_protected
    def register():
        data = request.get_json(silent=True) or request.form
        full_name = str(data.get("full_name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        if len(full_name) < 2 or len(full_name) > 120:
            return json_error("Name must be between 2 and 120 characters.")
        if "@" not in email or len(email) > 255:
            return json_error("Enter a valid email address.")
        if len(password) < 8:
            return json_error("Password must contain at least 8 characters.")
        if db.session.scalar(db.select(User).where(User.email == email)):
            return json_error("An account with this email already exists.", 409)
        user = User(full_name=full_name, email=email, role="user")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return jsonify(message="Registration successful.", user={"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}), 201

    @app.post("/api/auth/login")
    @csrf_protected
    def login():
        data = request.get_json(silent=True) or request.form
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        user = db.session.scalar(db.select(User).where(User.email == email))
        if not user or not user.check_password(password):
            return json_error("Invalid email or password.", 401)
        login_user(user, remember=False)
        return jsonify(message="Login successful.", role=user.role, redirect=url_for("admin_page") if user.role == "admin" else url_for("home"))

    @app.post("/api/auth/logout")
    @login_required
    @csrf_protected
    def logout():
        logout_user()
        session.clear()
        return jsonify(message="Logged out successfully.")

    @app.get("/api/auth/me")
    def me():
        if not current_user.is_authenticated:
            return jsonify(authenticated=False)
        return jsonify(authenticated=True, user={"id": current_user.id, "full_name": current_user.full_name, "email": current_user.email, "role": current_user.role})

    def validate_coordinates(latitude, longitude):
        if latitude in (None, "") and longitude in (None, ""):
            return None, None
        try:
            latitude, longitude = float(latitude), float(longitude)
        except (TypeError, ValueError):
            raise ValueError("GPS coordinates must be numeric.")
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("GPS coordinates are outside the valid range.")
        return latitude, longitude

    def save_upload(file):
        if not file or not file.filename:
            return None
        extension = Path(secure_filename(file.filename)).suffix.lower().lstrip(".")
        if extension not in app.config["ALLOWED_EXTENSIONS"]:
            raise ValueError("Only JPG, JPEG, PNG, WEBP, and GIF images are allowed.")
        expected_format = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP", "gif": "GIF"}[extension]
        try:
            image = Image.open(file.stream)
            if image.format != expected_format:
                raise ValueError("The image contents do not match the file extension.")
            if image.width * image.height > 30_000_000:
                raise ValueError("Image dimensions are too large; use an image under 30 megapixels.")
            image = ImageOps.exif_transpose(image)
            image.load()
            if image.format == "JPEG":
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")
            elif image.format in ("PNG", "WEBP") and image.mode not in ("RGB", "RGBA", "L"):
                image = image.convert("RGBA")
            elif image.format == "GIF":
                image.seek(0)
            safe_image = BytesIO()
            save_options = {"optimize": True} if expected_format in {"JPEG", "PNG", "GIF"} else {}
            image.save(safe_image, format=expected_format, **save_options)
        except ValueError:
            raise
        except (UnidentifiedImageError, OSError, EOFError, Image.DecompressionBombError) as error:
            raise ValueError("The uploaded file is not a valid supported image.") from error
        safe_image.seek(0)
        filename = f"{uuid4().hex}.{extension}"
        with (app.config["UPLOAD_FOLDER"] / filename).open("wb") as destination:
            destination.write(safe_image.getvalue())
        return filename

    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        safe_name = secure_filename(filename)
        if safe_name != filename or not safe_name:
            return json_error("Invalid file name.", 400)
        return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name)

    @app.post("/api/reports")
    @csrf_protected
    def create_report():
        data = request.form
        name = data.get("name", "").strip()
        location = data.get("location", "").strip()
        category = data.get("issue_type", "").strip()
        description = data.get("description", "").strip()
        if not name or not location or category not in app.config["ALLOWED_CATEGORIES"]:
            return json_error("Name, location, and a valid e-waste category are required.")
        if len(name) > 120 or len(location) > 255 or len(description) > 2000:
            return json_error("One or more fields exceed the allowed length.")
        try:
            latitude, longitude = validate_coordinates(data.get("latitude"), data.get("longitude"))
            filename = save_upload(request.files.get("image"))
        except ValueError as error:
            return json_error(str(error))
        report = Report(user_id=current_user.id if current_user.is_authenticated else None, name=name, location=location, issue_type=category, description=description or None, image_filename=filename, latitude=latitude, longitude=longitude)
        db.session.add(report)
        db.session.commit()
        return jsonify(message="Report submitted successfully.", issue_id=report.id, report=serialize_report(report)), 201

    @app.get("/api/reports")
    @login_required
    def user_reports():
        reports = db.session.scalars(db.select(Report).where(Report.user_id == current_user.id).order_by(Report.created_at.desc())).all()
        return jsonify(reports=[serialize_report(report) for report in reports])

    @app.get("/api/stats")
    def stats():
        total = db.session.scalar(db.select(func.count(Report.id))) or 0
        pending = db.session.scalar(db.select(func.count(Report.id)).where(Report.status == "Pending")) or 0
        in_progress = db.session.scalar(db.select(func.count(Report.id)).where(Report.status == "In Progress")) or 0
        resolved = db.session.scalar(db.select(func.count(Report.id)).where(Report.status == "Resolved")) or 0
        by_status = [{"status": status, "total": db.session.scalar(db.select(func.count(Report.id)).where(Report.status == status)) or 0} for status in app.config["ALLOWED_STATUSES"]]
        category_rows = db.session.execute(db.select(Report.issue_type, func.count(Report.id)).group_by(Report.issue_type)).all()
        recent_reports = db.session.scalars(db.select(Report).order_by(Report.created_at.desc()).limit(5)).all()
        recent = [
            {"id": item.id, "issue_type": item.issue_type, "status": item.status, "created_at": item.created_at.isoformat()}
            for item in recent_reports
        ]
        return jsonify(
            total_reported=total,
            pending=pending,
            in_progress=in_progress,
            resolved=resolved,
            categories_supported=len(app.config["ALLOWED_CATEGORIES"]),
            status=by_status,
            issues=[{"issue_type": category, "total": count} for category, count in category_rows],
            recent_reports=recent,
        )

    @app.get("/api/ai/model")
    def ai_model_info():
        return jsonify(get_classifier().metadata())

    @app.post("/api/ai/suggest-category")
    @csrf_protected
    def ai_suggest_category():
        data = request.get_json(silent=True) or {}
        description = str(data.get("text", "")).strip()
        if len(description) > 2000:
            return json_error("Description must be 2000 characters or fewer.")
        try:
            suggestion = get_classifier().predict(description)
        except ValueError as error:
            return json_error(str(error))
        return jsonify(suggestion)

    @app.get("/api/admin/reports")
    @admin_required
    def admin_reports():
        query = db.select(Report).order_by(Report.created_at.desc())
        status = request.args.get("status")
        category = request.args.get("category")
        search = request.args.get("search", "").strip()
        if status in app.config["ALLOWED_STATUSES"]:
            query = query.where(Report.status == status)
        if category in app.config["ALLOWED_CATEGORIES"]:
            query = query.where(Report.issue_type == category)
        if search:
            pattern = f"%{search}%"
            query = query.where(db.or_(Report.name.ilike(pattern), Report.location.ilike(pattern), Report.description.ilike(pattern)))
        reports = db.session.scalars(query).all()
        return jsonify(reports=[serialize_report(report) for report in reports])

    @app.put("/api/admin/reports/<int:report_id>")
    @admin_required
    @csrf_protected
    def update_report(report_id):
        report = db.session.get(Report, report_id)
        if not report:
            return json_error("Report not found.", 404)
        status = str((request.get_json(silent=True) or {}).get("status", ""))
        if status not in app.config["ALLOWED_STATUSES"]:
            return json_error("Invalid report status.")
        report.status = status
        db.session.commit()
        return jsonify(message="Report status updated.", report=serialize_report(report))

    @app.delete("/api/admin/reports/<int:report_id>")
    @admin_required
    @csrf_protected
    def delete_report(report_id):
        report = db.session.get(Report, report_id)
        if not report:
            return json_error("Report not found.", 404)
        filename = report.image_filename
        db.session.delete(report)
        db.session.commit()
        if filename:
            try:
                (app.config["UPLOAD_FOLDER"] / filename).unlink(missing_ok=True)
            except OSError:
                app.logger.warning("Could not remove uploaded file %s", filename)
        return jsonify(message="Report deleted successfully.")

    @app.post("/api/collections")
    @login_required
    @csrf_protected
    def create_collection():
        data = request.get_json(silent=True) or {}
        category = str(data.get("category", "")).strip()
        address = str(data.get("collection_address", "")).strip()
        notes = str(data.get("notes", "")).strip()
        try:
            preferred_date = date.fromisoformat(str(data.get("preferred_date", "")))
        except ValueError:
            return json_error("Choose a valid preferred collection date.")
        if category not in app.config["ALLOWED_CATEGORIES"] or not address or len(address) > 500:
            return json_error("A valid category and collection address are required.")
        if preferred_date < date.today():
            return json_error("Collection date cannot be in the past.")
        item = CollectionRequest(user_id=current_user.id, category=category, collection_address=address, preferred_date=preferred_date, notes=notes or None)
        db.session.add(item)
        db.session.commit()
        return jsonify(message="Collection request submitted.", request=serialize_collection(item)), 201

    @app.get("/api/collections")
    @login_required
    def collections():
        query = db.select(CollectionRequest).order_by(CollectionRequest.created_at.desc())
        if current_user.role != "admin":
            query = query.where(CollectionRequest.user_id == current_user.id)
        items = db.session.scalars(query).all()
        return jsonify(collection_requests=[serialize_collection(item) for item in items])

    @app.put("/api/admin/collections/<int:request_id>")
    @admin_required
    @csrf_protected
    def update_collection(request_id):
        item = db.session.get(CollectionRequest, request_id)
        if not item:
            return json_error("Collection request not found.", 404)
        status = str((request.get_json(silent=True) or {}).get("collection_status", ""))
        if status not in app.config["ALLOWED_COLLECTION_STATUSES"]:
            return json_error("Invalid collection status.")
        item.collection_status = status
        db.session.commit()
        return jsonify(message="Collection request updated.", request=serialize_collection(item))

    @app.cli.command("create-admin")
    def create_admin():
        email = input("Admin email: ").strip().lower()
        full_name = input("Admin full name: ").strip()
        password = input("Admin password (minimum 8 characters): ")
        if len(password) < 8:
            raise SystemExit("Password must contain at least 8 characters.")
        if db.session.scalar(db.select(User).where(User.email == email)):
            raise SystemExit("That email is already registered.")
        admin = User(full_name=full_name, email=email, role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print("Administrator account created.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
