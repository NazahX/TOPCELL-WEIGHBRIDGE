from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SerialSettingsPayload(BaseModel):
    port: Optional[str] = None
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = Field(default="N", pattern="^[NOEMS]$")
    stopbits: float = 1
    simulate: bool = False


class SerialSettingsResponse(SerialSettingsPayload):
    last_connected_at: Optional[datetime] = None
    connected: bool = False
    last_weight_kg: Optional[float] = None
    last_weight_time: Optional[datetime] = None


class WeighInRequest(BaseModel):
    vehicle_plate: str
    direction: str
    partner_name: str
    product_name: str
    operator_name: str
    gross_kg: Optional[float] = None
    weight_in_time: Optional[datetime] = None
    delivery_reference: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    remarks: Optional[str] = None


class WeighOutRequest(BaseModel):
    tare_kg: Optional[float] = None
    weight_out_time: Optional[datetime] = None
    remarks: Optional[str] = None


class TicketFinalizeRequest(BaseModel):
    qc_status: Optional[str] = None
    qc_note: Optional[str] = None
    remarks: Optional[str] = None


class TicketRead(BaseModel):
    id: int
    ticket_no: Optional[str]
    status: str
    direction: str
    vehicle_plate: str
    partner_name: str
    product_name: str
    delivery_reference: Optional[str]
    driver_name: Optional[str]
    driver_phone: Optional[str]
    operator_name: str
    gross_kg: float
    tare_kg: float
    net_kg: float
    weight_in_time: Optional[datetime]
    weight_out_time: Optional[datetime]
    qc_status: str
    qc_note: Optional[str]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyncQueueRead(BaseModel):
    id: int
    ticket_id: int
    status: str
    attempts: int
    last_error: Optional[str]
    last_attempt_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class WeightReading(BaseModel):
    weight_kg: Optional[float]
    captured_at: Optional[datetime]
    connected: bool
    source: str
