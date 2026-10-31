# Windows 10/11 setup guide

## 1. Install Python

Download Python from python.org. During installation, select **Add Python to PATH**. Open Command Prompt and verify:

```bat
python --version
```

## 2. Install Git

Install Git for Windows from git-scm.com and verify:

```bat
git --version
```

## 3. Install PostgreSQL

Download the Windows installer from postgresql.org. Set a password for the `postgres` superuser and remember it. Keep pgAdmin selected if you prefer a graphical database tool. Open SQL Shell (`psql`) or pgAdmin and run:

```sql
CREATE USER ecosmart_user WITH PASSWORD 'choose-a-password';
CREATE DATABASE ecosmart OWNER ecosmart_user;
CREATE DATABASE ecosmart_test OWNER ecosmart_user;
```

Use a real password locally; the example above is only a placeholder.

## 4. Open the project

Extract the ZIP, open the project folder in VS Code, and open its integrated terminal.

## 5–7. Create the environment and install dependencies

Command Prompt:

```bat
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, open PowerShell as your user and run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. You can also use Command Prompt instead.

## 8. Configure `.env`

```bat
copy .env.example .env
```

Edit `.env`:

- `SECRET_KEY`: a long random value used to sign sessions.
- `DATABASE_URL`: PostgreSQL connection string for the application database.
- `TEST_DATABASE_URL`: separate database used by PostgreSQL tests.
- `FLASK_DEBUG`: keep `false` except while debugging locally.
- `MAX_UPLOAD_SIZE`: maximum upload bytes; default is 5 MB.
- `UPLOAD_FOLDER`: directory for user uploads.

## 9–10. Migrate the database

```powershell
$env:FLASK_APP = "app.py"
flask db upgrade
```

If the command reports a connection error, verify PostgreSQL is running, the database exists, and the password in `.env` is correct.

## 11. Create an administrator

Do not use a public default admin password. Run:

```powershell
flask create-admin
```

Enter an email and a strong password when prompted.

## 12–14. Start and stop

```powershell
python run.py
```

Open `http://127.0.0.1:5000/`. Stop the server with `Ctrl+C`.

## 15. Troubleshooting

- **PostgreSQL connection error:** check the PostgreSQL service, database name, username, password, and port 5432.
- **Missing libraries:** activate `venv`, then run `pip install -r requirements.txt` again.
- **Port conflict:** set `PORT=5001` in `.env` and open port 5001.
- **Migration failure:** back up data, inspect the error, and verify that the database user owns the database.
- **Upload problem:** confirm `UPLOAD_FOLDER` is writable and the file is an allowed image under 5 MB.
- **Login problem:** use the exact email, reset the local database user password if needed, and confirm cookies are enabled.
