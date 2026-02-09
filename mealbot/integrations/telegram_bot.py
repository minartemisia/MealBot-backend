"""Telegram bot that sits on top of the Mealbot API.

Usage:
  export TELEGRAM_BOT_TOKEN="..."
  export MEALBOT_API_BASE="http://127.0.0.1:8000"
  python -m mealbot.integrations.telegram_bot

Notes:
  - Requires: python-telegram-bot
  - This forwards user text to POST /chat/message and returns reply.
"""

import os
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters


API_BASE = os.environ.get("MEALBOT_API_BASE", "http://127.0.0.1:8000")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Scrivi: pianifica 2026-03, spesa 2026-03, giorno 2026-03-05, ricetta 2026-03-05 cena")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        r = requests.post(f"{API_BASE}/chat/message", json={"text": text}, timeout=20)
        r.raise_for_status()
        reply = r.json().get("reply", "(nessuna risposta)")
    except Exception as e:
        reply = f"Errore nel contattare API: {e}"
    await update.message.reply_text(reply)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()


if __name__ == "__main__":
    main()
