# Deploy the Flask + PostgreSQL demo on Render

This project is a Python/Flask web application with session-based authentication and a PostgreSQL database. It is not a static-only website. Deploy the whole Flask app as a Python web service, rather than uploading these files to Netlify as a static site. Netlify would require a separate backend rewrite/integration; the current Flask routes, database sessions, and admin pages will not run as static HTML.

Official references: [Render Flask deployment guide](https://render.com/docs/deploy-flask), [Render PostgreSQL connection guide](https://render.com/docs/postgresql-creating-connecting), and [Netlify Functions overview](https://docs.netlify.com/build/functions/overview/).

Hosting plan availability, free quotas, sleep/retention rules, and prices can change. Check the provider's current plan details before creating services; a free AI library does not mean hosted PostgreSQL or durable file storage is free.

## Before deploying

1. Push the cleaned project to GitHub. Confirm `.env` is ignored and never present in the repository history with valid credentials.
2. In the hosting provider, create a PostgreSQL database. If available, place the web service and database in the same region.
3. Create a Python Web Service connected to the existing GitHub repository and `main` branch.
4. Use this build command:

   ```text
   pip install -r requirements.txt
   ```

5. Use this start command:

   ```text
   gunicorn app:app
   ```

## Environment variables

Set these in the web-service dashboard, not in a committed `.env` file:

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `SECRET_KEY` | A unique, randomly generated secret with at least 32 characters. Do not reuse a password. |
| `DATABASE_URL` | The private/internal URL for the managed PostgreSQL database. The app converts common `postgres://` / `postgresql://` URLs to the Psycopg 3 driver form. |
| `SESSION_COOKIE_SECURE` | `true` (the production default; requires HTTPS) |
| `CORS_ORIGINS` | Leave blank when the Flask app serves its own pages. If you later host a separate frontend, set only its exact HTTPS origin. |

Do not set `FLASK_DEBUG=true` in production.

## Database and admin setup

After the service starts, use its Shell/Console to apply the initial schema:

```sh
flask --app app db upgrade
```

Create an administrator interactively from the same Shell/Console:

```sh
flask --app app create-admin
```

Use a unique admin email and password. Do not add administrator credentials to source code or `README.md`. For future schema changes, create and commit a migration locally, then apply it to the hosted database.

Set the provider's health-check path to:

```text
/api/health
```

Then test `/`, `/api/health`, login, report submission, an AI suggestion, and the admin dashboard in a private browser window. The AI inference stays inside the Flask service; it does not require an API key.

## Important demo limitations

- Uploaded photos are stored on the service's local filesystem by default. Many hosted web services have ephemeral disks, so photos may disappear after a redeploy/restart. Do not promise durable photo storage until you configure a supported persistent disk or object-storage service and review its cost.
- The collection request is a database workflow only. No real pickup is dispatched.
- The AI training rows are synthetic. The classifier is a demonstration, not a production decision system.
- Use fictional names, addresses, and photos in a public portfolio demo. Do not publish real user-submitted personal information.
