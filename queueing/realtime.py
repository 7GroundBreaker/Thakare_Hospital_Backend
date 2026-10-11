"""Live push to the waiting-room display via Supabase Realtime Broadcast.

The backend runs on serverless functions, which cannot hold WebSocket/SSE
connections, so it publishes a tiny "changed" event to a Supabase Realtime
channel and the display (subscribed over a websocket) re-fetches the public
display endpoint. The event carries no data, so a spoofed broadcast can at
most trigger a harmless refresh. Without SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY
this is a no-op and the display falls back to polling.
"""

import json
import logging
import urllib.request

from django.conf import settings
from django.db import transaction

logger = logging.getLogger("thakare_hospital")


def _send():
    url = settings.SUPABASE_URL.rstrip("/") + "/realtime/v1/api/broadcast"
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    body = json.dumps(
        {
            "messages": [
                {"topic": settings.QUEUE_REALTIME_CHANNEL, "event": "changed", "payload": {}}
            ]
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=3):
            pass
    except Exception:
        # The display still catches up through its fallback polling.
        logger.warning("Queue realtime broadcast failed", exc_info=True)


def notify_display_changed():
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        transaction.on_commit(_send)
