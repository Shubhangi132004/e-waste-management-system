# Learning guide

## Flask

`create_app` builds the application and registers configuration, extensions, routes, and error handlers. A route maps an HTTP method and URL to a Python function. JSON responses communicate with the JavaScript frontend.

## SQLAlchemy and PostgreSQL

Models describe tables as Python classes. `db.session.add`, `commit`, and `select` create and query records without handwritten SQL. PostgreSQL enforces relationships, unique email addresses, timestamps, indexes, and foreign keys. Flask-Migrate stores schema changes as reviewable revisions.

## Authentication

Flask-Login stores a signed session cookie after login. Passwords are never stored directly; Werkzeug stores one-way password hashes. `@login_required` checks login, while the project’s `admin_required` decorator checks the role on the server.

## Validation and security

The frontend improves usability, but the backend is the authority. It validates categories, field lengths, dates, coordinates, statuses, and uploads. CSRF tokens protect state-changing browser requests. Random upload filenames avoid collisions, and `secure_filename` prevents path traversal.

## HTML and CSS

The existing page is semantic HTML with CSS variables, responsive media queries, reusable cards, and a green environmental palette. The upgraded pages add accessible error and empty states without replacing the original visual direction.

## JavaScript

`apiFetch` centralizes API errors and CSRF handling. Admin rows are built with `textContent` and DOM methods rather than inserting user data through `innerHTML`. Charts are created from live `/api/stats` values, so an empty database shows zero rather than fake values.

## PostgreSQL concepts to explain

A primary key uniquely identifies a record. A foreign key connects records. A unique constraint prevents duplicate emails. An index speeds up common filters such as status and category. A migration is a repeatable versioned change to the schema.
