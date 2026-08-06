import logging

import httpx

from app.core.config import get_settings
from app.domain.contact_request import ContactRequest

logger = logging.getLogger(__name__)

_RESEND_API_URL = "https://api.resend.com/emails"


async def send_contact_notification_email(contact: ContactRequest) -> None:
    """Notify the admin of a new contact request via Resend.

    API.md - POST /contact: sending is asynchronous relative to the HTTP
    response, and a provider failure must never prevent the request from
    being recorded. Callers must schedule this (e.g. via BackgroundTasks)
    rather than await it inline, and this function never raises — any
    failure (missing config, network error, non-2xx from Resend) is logged
    and swallowed.
    """
    settings = get_settings()
    if settings.resend_api_key is None or settings.contact_notification_email is None:
        logger.info("Skipping contact notification email: Resend is not configured.")
        return

    payload = {
        "from": settings.contact_notification_from,
        "to": [settings.contact_notification_email],
        "subject": f"Nueva solicitud de contacto: {contact.subject or contact.name}",
        "text": (
            f"Nombre: {contact.name}\n"
            f"Email: {contact.email}\n"
            f"Empresa: {contact.company or '-'}\n\n"
            f"{contact.message}"
        ),
    }
    headers = {"Authorization": f"Bearer {settings.resend_api_key}"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(_RESEND_API_URL, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError:
        logger.exception(
            "Failed to send contact notification email for contact request %s",
            contact.id,
        )
