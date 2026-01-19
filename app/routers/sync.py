import asyncio

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import SyncQueue
from app.schemas import SyncQueueRead
from app.services.sync_service import sync_service

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.get("/queue", response_model=list[SyncQueueRead])
def list_queue(session: Session = Depends(get_session)) -> list[SyncQueueRead]:
    return session.exec(select(SyncQueue).order_by(SyncQueue.created_at.desc())).all()


@router.post("/run")
async def run_sync_now() -> dict:
    await sync_service.sync_pending()
    return {"status": "ok"}
