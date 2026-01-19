import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.routers import serial, sync, tickets, weight
from app.services.sync_service import sync_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Topcell Weighbridge")
settings = get_settings()
static_dir = Path(__file__).resolve().parent / "static"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(serial.router)
app.include_router(weight.router)
app.include_router(sync.router)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    sync_service.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await sync_service.shutdown()


@app.get("/", include_in_schema=False)
async def serve_ui() -> FileResponse:
    index = static_dir / "index.html"
    return FileResponse(index)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
