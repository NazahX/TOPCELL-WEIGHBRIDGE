from fastapi import APIRouter

from app.schemas import WeightReading
from app.services.serial_manager import serial_manager

router = APIRouter(prefix="/api/weight", tags=["weight"])


@router.get("/live", response_model=WeightReading)
def get_live_weight() -> WeightReading:
    return serial_manager.get_reading()
