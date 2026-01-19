import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.config import get_settings
from app.database import engine
from app.models import SyncQueue, Ticket
from app.services.odoo_client import OdooClient

logger = logging.getLogger("sync_service")


class SyncService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OdooClient()
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run_loop())

    async def shutdown(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self) -> None:
        while True:
            try:
                await self.sync_pending()
            except Exception:
                logger.exception("Sync loop encountered an error")
            await asyncio.sleep(self.settings.sync_interval_seconds)

    async def sync_pending(self) -> None:
        with Session(engine) as session:
            pending = session.exec(
                select(SyncQueue).where(SyncQueue.status == "pending").order_by(SyncQueue.created_at)
            ).all()

            for item in pending:
                await self._process_item(session, item)

    async def _process_item(self, session: Session, item: SyncQueue) -> None:
        item.attempts += 1
        item.last_attempt_at = datetime.utcnow()
        payload = json.loads(item.payload)

        try:
            result = await self.client.send_ticket(payload)
            item.status = "sent"
            item.last_error = None

            # If Odoo returns an external id, persist it for audit
            ticket = session.get(Ticket, item.ticket_id)
            if ticket and isinstance(result, dict) and result.get("external_id"):
                ticket.odoo_external_id = str(result["external_id"])
                ticket.updated_at = datetime.utcnow()

            session.add(item)
            session.commit()
        except Exception as exc:
            item.status = "failed"
            item.last_error = str(exc)
            session.add(item)
            session.commit()
            logger.warning("Sync failed for ticket %s: %s", item.ticket_id, exc)

    def enqueue_ticket(self, session: Session, ticket: Ticket) -> SyncQueue:
        payload = self._ticket_payload(ticket)
        record = SyncQueue(ticket_id=ticket.id, payload=json.dumps(payload), status="pending")
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def _ticket_payload(self, ticket: Ticket) -> dict:
        return {
            "ticket_no": ticket.ticket_no,
            "vehicle_plate": ticket.vehicle_plate,
            "direction": ticket.direction,
            "partner_name": ticket.partner_name,
            "product_name": ticket.product_name,
            "gross_kg": ticket.gross_kg,
            "tare_kg": ticket.tare_kg,
            "net_kg": ticket.net_kg,
            "weight_in_time": ticket.weight_in_time.isoformat() if ticket.weight_in_time else None,
            "weight_out_time": ticket.weight_out_time.isoformat() if ticket.weight_out_time else None,
            "operator_name": ticket.operator_name,
            "delivery_reference": ticket.delivery_reference,
            "driver_name": ticket.driver_name,
            "driver_phone": ticket.driver_phone,
            "remarks": ticket.remarks,
            "qc_status": ticket.qc_status,
            "qc_note": ticket.qc_note,
        }


sync_service = SyncService()
