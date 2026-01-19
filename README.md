# Topcell Weighbridge (FastAPI)

Desktop-ready weighbridge control app for TOPCELL Nigeria. Runs a local FastAPI backend with a browser UI (served locally) to capture gross/tare weights from a serial indicator, finalize tickets, and sync to Odoo with an offline queue.

## Quick start (dev)
1) Create a virtualenv and install deps:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```
2) Run the backend with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
3) Open http://localhost:8000 to use the web UI (served from `app/static/`).

## Key features
- Serial/RS232 support via pyserial with live weight cache (optional simulated feed for dev/offline).
- Ticket lifecycle: weigh-in (gross) ➜ weigh-out (tare) ➜ finalize (locks, computes net, queues for sync).
- SQLite persistence (`app/data/weighbridge.db`) with audit-friendly fields and optional QC notes.
- Offline-first sync queue to Odoo using REST; runs in the background and can be triggered manually.
- Simple browser UI for operators; packaged later with PyInstaller for Windows 7 deployment.

## API highlights
- `POST /api/tickets/weigh-in` – create gross record (uses live weight if `gross_kg` omitted).
- `POST /api/tickets/{id}/weigh-out` – capture tare (uses live weight if `tare_kg` omitted).
- `POST /api/tickets/{id}/finalize` – compute net, lock ticket, enqueue for sync.
- `GET /api/weight/live` – live indicator cache.
- `POST /api/serial/connect` – configure COM port + connect (or enable simulation).
- `POST /api/sync/run` – force a sync attempt.

## Odoo configuration
Set these in a `.env` file or environment variables:
- `ODOO_BASE_URL=https://your-odoo-host`
- `ODOO_API_KEY=...`
- `ODOO_DB=...` (if needed by your endpoint)
- `ODOO_USERNAME=...`

The Odoo endpoint expected is `/api/weighbridge/tickets` (adjust in `app/services/odoo_client.py` if different).

## Packaging for Windows 7 (outline)
- Install PyInstaller inside the venv: `pip install pyinstaller`.
- Build: `pyinstaller --onefile --name TopcellWeighbridge app/main.py`.
- Bundle `app/static/` and `app/data/` as needed (e.g., via `--add-data "app/static;app/static"`). A more tailored spec file can be added once installer requirements are finalized.

## Project layout
- `app/main.py` – FastAPI app wiring, static UI.
- `app/models.py` – SQLModel definitions for tickets, sync queue, serial settings.
- `app/services/serial_manager.py` – live serial reading + simulator.
- `app/services/sync_service.py` – background sync loop & queue.
- `app/static/` – UI assets for browser operators.
