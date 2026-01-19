from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config import get_settings
from app.database import get_session
from app.models import SerialSettings
from app.schemas import SerialSettingsPayload, SerialSettingsResponse
from app.services.serial_manager import serial_manager

router = APIRouter(prefix="/api/serial", tags=["serial"])


def _get_or_create_serial_settings(session: Session) -> SerialSettings:
    settings = session.get(SerialSettings, 1)
    if not settings:
        app_settings = get_settings()
        settings = SerialSettings(id=1, simulate=app_settings.allow_weight_simulation)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@router.get("/settings", response_model=SerialSettingsResponse)
def get_serial_settings(session: Session = Depends(get_session)) -> SerialSettingsResponse:
    stored = _get_or_create_serial_settings(session)
    reading = serial_manager.get_reading()
    return SerialSettingsResponse(
        port=stored.port,
        baudrate=stored.baudrate,
        bytesize=stored.bytesize,
        parity=stored.parity,
        stopbits=stored.stopbits,
        simulate=stored.simulate,
        last_connected_at=stored.last_connected_at,
        connected=reading.connected,
        last_weight_kg=reading.weight_kg,
        last_weight_time=reading.captured_at,
    )


@router.post("/connect", response_model=SerialSettingsResponse)
def connect_serial(
    payload: SerialSettingsPayload, session: Session = Depends(get_session)
) -> SerialSettingsResponse:
    stored = _get_or_create_serial_settings(session)
    serial_manager.configure(payload)
    try:
        serial_manager.connect()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    stored.port = payload.port
    stored.baudrate = payload.baudrate
    stored.bytesize = payload.bytesize
    stored.parity = payload.parity
    stored.stopbits = payload.stopbits
    stored.simulate = payload.simulate
    stored.last_connected_at = datetime.utcnow() if not payload.simulate else None
    session.add(stored)
    session.commit()
    session.refresh(stored)

    reading = serial_manager.get_reading()
    return SerialSettingsResponse(
        **payload.model_dump(),
        last_connected_at=stored.last_connected_at,
        connected=reading.connected,
        last_weight_kg=reading.weight_kg,
        last_weight_time=reading.captured_at,
    )


@router.post("/disconnect")
def disconnect_serial(session: Session = Depends(get_session)) -> dict:
    serial_manager.disconnect()
    stored = _get_or_create_serial_settings(session)
    stored.last_connected_at = None
    session.add(stored)
    session.commit()
    return {"connected": False}
