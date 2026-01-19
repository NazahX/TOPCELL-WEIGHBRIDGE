from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from app.models import Ticket


def generate_ticket_number(session: Session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"WB{today}"
    last_ticket = session.exec(
        select(Ticket)
        .where(Ticket.ticket_no.like(f"{prefix}%"))
        .order_by(Ticket.ticket_no.desc())
        .limit(1)
    ).first()

    if last_ticket and last_ticket.ticket_no:
        suffix = last_ticket.ticket_no.split("-")[-1]
        try:
            seq = int(suffix) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1

    return f"{prefix}-{seq:04d}"


def create_weigh_in(
    session: Session, data: dict, gross_kg: float, weight_in_time: Optional[datetime]
) -> Ticket:
    ticket = Ticket(
        status="weigh_in",
        gross_kg=gross_kg,
        weight_in_time=weight_in_time or datetime.utcnow(),
        updated_at=datetime.utcnow(),
        **data,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def record_weigh_out(
    session: Session, ticket: Ticket, tare_kg: float, weight_out_time: Optional[datetime]
) -> Ticket:
    ticket.tare_kg = tare_kg
    ticket.weight_out_time = weight_out_time or datetime.utcnow()
    ticket.status = "weigh_out"
    ticket.updated_at = datetime.utcnow()
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def finalize_ticket(
    session: Session, ticket: Ticket, qc_status: Optional[str], qc_note: Optional[str], remarks: Optional[str]
) -> Ticket:
    if ticket.gross_kg <= 0 or ticket.tare_kg <= 0:
        raise ValueError("Gross and tare weights must be recorded before finalizing")

    net = ticket.gross_kg - ticket.tare_kg
    if net < 0:
        raise ValueError("Computed net weight is negative; check captured weights")

    ticket.net_kg = net
    ticket.ticket_no = ticket.ticket_no or generate_ticket_number(session)
    ticket.qc_status = qc_status or ticket.qc_status
    ticket.qc_note = qc_note or ticket.qc_note
    ticket.remarks = remarks or ticket.remarks
    ticket.status = "finalized"
    ticket.updated_at = datetime.utcnow()
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def list_tickets(session: Session, limit: int = 50) -> List[Ticket]:
    return session.exec(select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)).all()
