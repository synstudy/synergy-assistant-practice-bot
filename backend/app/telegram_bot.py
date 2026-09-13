import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from . import storage
from .dialog import DialogEngine
from .knowledge import KnowledgeBase

knowledge_base = KnowledgeBase.load()
engine = DialogEngine(knowledge_base)


def _session_id(update: Update):
    return f"tg:{update.effective_chat.id}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage.reset_session(_session_id(update))
    await update.message.reply_text(engine.welcome())


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage.reset_session(_session_id(update))
    await update.message.reply_text("Начнём заново. Чем могу помочь?")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(engine.help_text())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = engine.process(_session_id(update), update.message.text)
    reply = result["reply"]
    if result["quick_replies"]:
        reply += "\n\nВарианты: " + " • ".join(result["quick_replies"])
    await update.message.reply_text(reply)


def main():
    storage.init_db()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN не задан")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler(["start"], start))
    application.add_handler(CommandHandler(["reset", "restart"], reset))
    application.add_handler(CommandHandler(["help"], help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()


if __name__ == "__main__":
    main()
