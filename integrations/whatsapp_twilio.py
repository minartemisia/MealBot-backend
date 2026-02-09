"""WhatsApp (Twilio) webhook integration for Mealbot.

This runs a tiny FastAPI app that receives WhatsApp messages from Twilio,
forwards the body to Mealbot's /chat/message endpoint, and responds.

Prerequisites:
  - Twilio WhatsApp sandbox or approved WhatsApp sender.
  - Public URL for your webhook (ngrok / cloud).

Env:
  MEALBOT_API_BASE="http://127.0.0.1:8000"

Run:
  pip install fastapi uvicorn requests
  uvicorn mealbot.integrations.whatsapp_twilio:app --reload --port 9000
"""

import os
import requests
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse


API_BASE = os.environ.get("MEALBOT_API_BASE", "http://127.0.0.1:8000")

app = FastAPI(title="Mealbot WhatsApp (Twilio) Webhook")


@app.post("/twilio", response_class=PlainTextResponse)
def twilio_webhook(Body: str = Form("")):
    # Twilio sends the message text in 'Body'
    text = (Body or "").strip()
    if not text:
        return ""
    try:
        r = requests.post(f"{API_BASE}/chat/message", json={"text": text}, timeout=20)
        r.raise_for_status()
        reply = r.json().get("reply", "")
    except Exception as e:
        reply = f"Errore nel contattare API: {e}"

    # Twilio expects TwiML. Minimal compliant response:
    return f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message>{_xml_escape(reply)}</Message></Response>"


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;"))
