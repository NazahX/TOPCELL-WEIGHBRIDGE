import httpx

from app.config import get_settings


class OdooClient:
    """
    Minimal REST client for Odoo. This assumes an HTTP endpoint is exposed for
    weighbridge tickets. Adjust the endpoint path in `send_ticket` to match the
    Odoo deployment.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_ticket(self, payload: dict) -> dict:
        if not self.settings.odoo_base_url or not self.settings.odoo_api_key:
            raise RuntimeError("Odoo connection is not configured")

        url = f"{self.settings.odoo_base_url.rstrip('/')}/api/weighbridge/tickets"
        headers = {
            "Authorization": f"Bearer {self.settings.odoo_api_key}",
            "X-ODOO-DB": self.settings.odoo_db or "",
            "X-ODOO-USER": self.settings.odoo_username or "",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
