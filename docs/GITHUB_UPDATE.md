# Update the existing GitHub repository on Windows

Your original project has already been pushed to `main`. This is an update to that repository; do not create another repository.

## 1. Keep a backup and stop the app

In VS Code's PowerShell terminal, press `Ctrl+C` if Flask is running. Make a copy of your project folder as a backup.

## 2. Copy the update files into the existing clone

Download the clean updated project ZIP, extract it to a temporary folder, then copy its contents into the root of your existing Git clone (the folder containing `app.py` and `.git`). Allow project files to be replaced. The ZIP intentionally does **not** contain `.git`, `.env`, your virtual environment, or an `uploads` folder, so your Git history and local configuration stay separate.

Do not delete or replace your local `.env`. It holds your own database connection and must stay on your computer, not in GitHub.

## 3. Install the new dependencies and run checks

From the repository root in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
flask --app app db upgrade
pytest -q
python -m ai.evaluate_category_model
python run.py
```

If your virtual environment folder is named `.venv`, use `.\.venv\Scripts\Activate.ps1` instead. The local AI feature has no API key. The evaluation script reports metrics only for its bundled synthetic examples.

Open `http://127.0.0.1:5000/`. Try an e-waste report using fictional details, request a category suggestion, and check `/api/health`. Use a separate PostgreSQL test database if you set `TEST_DATABASE_URL` to PostgreSQL; the supplied example uses in-memory SQLite for tests.

## 4. Commit and push the update

Check the files before staging:

```powershell
git status --short
git check-ignore -v .env
git diff --stat
```

`git check-ignore -v .env` should show `.gitignore`. `git status --short` must not list `.env`, database dumps, or uploaded user files. Then:

```powershell
git add -A
git status --short
git diff --cached --stat
git commit -m "Add offline e-waste AI and improve report workflow"
git push origin main
```

If `git status` shows `.env` as staged or tracked, stop and remove it from the staging area before committing. Never paste its contents into a chat or put it in a screenshot.
