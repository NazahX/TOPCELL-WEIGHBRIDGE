from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Ticket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_no: Optional[str] = Field(default=None, index=True, unique=True)
    status: str = Field(default="weigh_in", index=True)
    direction: str = Field(index=True)
    vehicle_plate: str = Field(index=True)
    partner_name: str
    product_name: str
    delivery_reference: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    operator_name: str
    gross_kg: float = 0
    tare_kg: float = 0
    net_kg: float = 0
    weight_in_time: Optional[datetime] = None
    weight_out_time: Optional[datetime] = None
    qc_status: str = Field(default="pending")
    qc_note: Optional[str] = None
    remarks: Optional[str] = None
    attachment_path: Optional[str] = None
    odoo_external_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SyncQueue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="ticket.id", index=True)
    payload: str
    status: str = Field(default="pending", index=True)
    attempts: int = 0
    last_error: Optional[str] = None
    last_attempt_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SerialSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    port: Optional[str] = None
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: float = 1
    simulate: bool = False
    last_connected_at: Optional[datetime] = None
