# Farmer Seed Distribution Platform

A small Python Flask application for managing farmers, seed inventory, and subsidized seed distribution.

## Features

- Register farmers with village, phone, land size, and crop preference.
- Maintain seed inventory with season, variety, stock, price, and reorder level.
- Record seed distributions with subsidy calculation.
- Automatically reduce inventory after each distribution.
- Dashboard for total farmers, available seed stock, distributed quantity, and low-stock alerts.
- Reports by crop type and village.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

The SQLite database is created automatically as `seed_platform.db` on first run.
