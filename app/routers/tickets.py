from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Ticket
from app.schemas import TicketFinalizeRequest, TicketRead, WeighInRequest, WeighOutRequest
from app.services import ticket_service
from app.services.serial_manager import serial_manager
from app.services.sync_service import sync_service

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketRead])
def list_recent_tickets(limit: int = 50, session: Session = Depends(get_session)) -> list[TicketRead]:
    return ticket_service.list_tickets(session, limit=limit)


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, session: Session = Depends(get_session)) -> TicketRead:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/weigh-in", response_model=TicketRead)
def create_weigh_in_ticket(payload: WeighInRequest, session: Session = Depends(get_session)) -> TicketRead:
    weight = payload.gross_kg
    if weight is None:
        live = serial_manager.get_reading()
        if live.weight_kg is None:
            raise HTTPException(status_code=400, detail="No live weight available from indicator")
        weight = live.weight_kg

    data = payload.model_dump()
    data.pop("gross_kg", None)
    data.pop("weight_in_time", None)

    if weight <= 0:
        raise HTTPException(status_code=400, detail="Gross weight must be greater than zero")

    ticket = ticket_service.create_weigh_in(session, data, weight, payload.weight_in_time)
    return ticket


@router.post("/{ticket_id}/weigh-out", response_model=TicketRead)
def add_tare_weight(
    ticket_id: int, payload: WeighOutRequest, session: Session = Depends(get_session)
) -> TicketRead:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    tare = payload.tare_kg
    if tare is None:
        live = serial_manager.get_reading()
        if live.weight_kg is None:
            raise HTTPException(status_code=400, detail="No live weight available from indicator")
        tare = live.weight_kg

    if tare <= 0:
        raise HTTPException(status_code=400, detail="Tare weight must be greater than zero")

    ticket = ticket_service.record_weigh_out(session, ticket, tare, payload.weight_out_time)
    return ticket


@router.post("/{ticket_id}/finalize", response_model=TicketRead)
def finalize_ticket(
    ticket_id: int, payload: TicketFinalizeRequest, session: Session = Depends(get_session)
) -> TicketRead:
    ticket = session.exec(select(Ticket).where(Ticket.id == ticket_id)).one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.status == "finalized":
        return ticket

    try:
        ticket = ticket_service.finalize_ticket(session, ticket, payload.qc_status, payload.qc_note, payload.remarks)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    sync_service.enqueue_ticket(session, ticket)
    return ticket
