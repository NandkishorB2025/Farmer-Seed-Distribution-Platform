# Farmer Seed Distribution Platform

The Farmer Seed Distribution Platform is the first application in a planned enterprise low-code/no-code platform.
The current implementation is a Flask application that is being refactored into a clean, feature-based architecture.

## Features

- Register farmers with village, phone, land size, and crop preference.
- Maintain seed inventory with season, variety, stock, price, and reorder level.
- Record seed distributions with subsidy calculation.
- Automatically reduce inventory after each distribution.
- Dashboard for total farmers, available seed stock, distributed quantity, and low-stock alerts.
- Reports by crop type and village.

## Architecture

```text
seed_platform/
  core/
    app_factory.py      Flask application factory
    config.py           Environment-driven configuration
    database.py         Database lifecycle and shared query helpers
  modules/
    seed_portal/
      routes.py         HTTP controllers
      services.py       Business workflows and validation
      repositories.py   Data access
      schema.sql        Current SQLite schema
templates/             Shared server-rendered UI templates
static/                Shared CSS assets
tests/                 Smoke and service tests
```

The current database is SQLite to keep the first refactor low-risk. The target platform database is Supabase PostgreSQL with migrations, UUID primary keys, row-level security, soft delete, and audit logging.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

The SQLite database is created automatically as `seed_platform.db` on first run.

## Test

```powershell
pytest
```

## Platform Roadmap

1. Replace SQLite schema initialization with migration-managed PostgreSQL/Supabase.
2. Introduce authentication, roles, permission matrix, and audit logging.
3. Create metadata tables for applications, forms, menus, reports, dashboards, workflows, and rules.
4. Convert hardcoded Seed Distribution Portal screens into metadata-driven dynamic forms and views.
5. Add deployment assets for Docker backend, Vercel frontend, and GitHub Actions.
