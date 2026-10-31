# EcoSmart — E-Waste Reporting and Collection Workflow

**Developer:** Subhangi Solunke  
**Project type:** Engineering academic project  
**Domain:** Artificial Intelligence and Data Science

EcoSmart is a full-stack academic prototype for reporting electronic waste, tracking report status, and requesting collection. It combines a Flask API, PostgreSQL persistence, a responsive web interface, and an optional locally executed text-classification feature that suggests an e-waste category.

> This is a student project, not a municipal or CPCB service. It does not dispatch collection vehicles, verify recyclers, or provide regulatory advice. Use fictional data in any public demo.

> **Provenance:** The submitted project documentation states that this repository was adapted and further developed from a supplied student project. Keep this note and any original contributor or third-party notices accurate. No project reuse license is included yet.

## What it does

- Accepts e-waste reports with category, description, optional image, and optional coordinates.
- Supports registration, login, report history, and collection-request tracking.
- Gives administrators protected report search, status updates, deletion, live database counts, charts, and PDF export.
- Suggests a category from a description with a local TF-IDF + logistic-regression model. The suggestion is optional and must be confirmed by the user.
- Uses PostgreSQL with SQLAlchemy and versioned Flask-Migrate migrations.
- Includes CSRF checks for state-changing browser requests, hashed passwords, server-side admin authorization, input validation, upload-size limits, and image-content validation/re-encoding before storage.

## AI/data-science component

The classifier is CPU-only and runs in the Flask application. It uses scikit-learn and a bundled CSV containing **84 synthetic, manually authored examples** across seven categories. No paid model API is used. The sample set is for demonstrating the pipeline only and is not representative of real e-waste reports. Returned model scores are not calibrated probabilities and should not be treated as guarantees.

Run the reproducible five-fold evaluation from the project root:

```powershell
python -m ai.evaluate_category_model
```

The script reports a classification report and confusion matrix on the synthetic examples. Do not claim that those metrics represent real-world performance. See [docs/AI_MODEL.md](docs/AI_MODEL.md) for the method, limitations, and improvement plan.

## Technology and architecture

- Python 3.11+, Flask, Flask-Login, Flask-SQLAlchemy, Flask-Migrate
- PostgreSQL via Psycopg 3
- scikit-learn: TF-IDF features and logistic regression; Pillow: image validation and re-encoding; Gunicorn: production WSGI serving
- HTML, CSS, vanilla JavaScript, Chart.js
- Pytest

```text
Browser (HTML/CSS/JS)
  ├─ same-origin JSON/multipart requests + CSRF token
  ├─ Flask routes: validation, authentication, admin permissions, AI suggestion
  └─ SQLAlchemy ── PostgreSQL
       ├─ users
       ├─ reports
       └─ collection_requests

AI inference runs inside the Flask process from the bundled local sample corpus.
```

## Run on Windows

Open PowerShell in the repository folder, then:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Install PostgreSQL and create a development database. Edit `.env` locally with a strong unique `SECRET_KEY` and your own PostgreSQL connection URL. **Never commit `.env` or paste its contents into a chat.** The sample config runs tests against in-memory SQLite. If you override `TEST_DATABASE_URL`, point it to a separate test database, never your development database.

Apply migrations, create the admin account, and start the local server:

```powershell
flask --app app db upgrade
flask --app app create-admin
python run.py
```

Visit `http://127.0.0.1:5000/`. The local health endpoint is `http://127.0.0.1:5000/api/health`. The admin page is available after sign-in at `/admin`.

## Run checks

```powershell
pytest -q
python -m ai.evaluate_category_model
```

Tests use an isolated SQLite database unless `TEST_DATABASE_URL` is provided. Passing route tests is not the same as a production security or privacy audit.

## API overview

`GET /api/health` checks database connectivity. `GET /api/stats` returns database-backed report totals, status counts, categories, and recent report activity without exposing submitter names or exact addresses. `GET /api/ai/model` describes the local classifier. `POST /api/ai/suggest-category` accepts a short text description and requires a CSRF token. See [docs/API.md](docs/API.md) for the complete route list.

## Project structure

```text
app.py                         Flask application and JSON routes
models.py                      SQLAlchemy models
config.py                      Environment-based configuration
migrations/                    Database schema history
index.html                     E-waste reporting interface
style.css / admin.css          Responsive UI styling
script.js / auth.js / admin.js Browser interactions
ai/category_classifier.py      Local text-classification pipeline
ai/evaluate_category_model.py  Reproducible cross-validation report
data/category_training_samples.csv  Synthetic teaching dataset
tests/                         API and model-integration tests
docs/AI_MODEL.md               AI method and limitations
docs/GITHUB_UPDATE.md          Windows steps to update and push this repository
docs/DEPLOY_RENDER.md           Flask/PostgreSQL hosting steps
.env.example                   Safe environment-variable template
```

## Deployment and safety

Use a Python web-service host and managed PostgreSQL for the existing Flask application; static hosting alone will not run the backend. Configure production secrets in the host dashboard, require HTTPS, apply migrations, and decide on durable storage for uploads before inviting public use. Local filesystem uploads can be lost when a hosted service restarts or redeploys. The demo has no external collection, email, or recycler integration.

See [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) for step-by-step Python web-service deployment instructions and current configuration requirements. Hosting-plan prices and free quotas can change; verify them before deployment.

For Indian regulatory information, use the official [CPCB e-waste rules page](https://cpcb.nic.in/rules-6/) and [CPCB e-waste FAQ](https://eprewaste.cpcb.gov.in/assets/PDF/faqewaste.pdf). EcoSmart is not affiliated with CPCB.

Before publishing, choose a project license if you want to grant others reuse rights. Public visibility alone does not grant an open-source license.
