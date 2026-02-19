import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from langchain_core.messages import HumanMessage, AIMessage

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.hotel_agent import run_hotel_agent
from utils.helpers import initialize_hotel
from config.settings import settings

from database.connection import SessionLocal
from database.repository import HotelRepository
from database.models import ReservationDB  # ← ADD THIS IMPORT

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    user_id = str(user.id)  # ← Convert to string

    # Clear DB session on /start
    with SessionLocal() as db:
        repo = HotelRepository(db)
        repo.clear_chat_history(user_id)

    with SessionLocal() as db:
        repo = HotelRepository(db)
        hotel = repo.load_hotel(settings.HOTEL_NAME)

    welcome_message = (
        f"👋 Hello, {user.first_name}! Welcome to {hotel.name}.\n\n"
        "I'm your AI concierge. I can help you with:\n"
        "🏨 Check room availability\n"
        "📅 Make reservations\n"
        "❌ Cancel reservations\n"
        "ℹ️ Room information\n\n"
        "How can I assist you today?\n\n"
        "Type /help for available commands."
    )

    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🤖 *Hotel AI Assistant Commands*\n\n"
        "/start - Start a new conversation\n"
        "/help - Show this help message\n"
        "/reservations - View all current reservations\n"
        "/rooms - View all available room types\n"
        "/clear - Clear your conversation history\n\n"
        "*Example requests:*\n"
        "• 'What rooms are available from 10/03/2026 to 15/03/2026?'\n"
        "• 'Book room 201 for 2 guests'\n"
        "• 'Cancel reservation 1'\n\n"
        "I understand English, Georgian (ქართული), and Russian (Русский)! 🌍"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def rooms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rooms command - show all rooms."""
    user_id = str(update.effective_user.id)

    with SessionLocal() as db:
        repo = HotelRepository(db)
        hotel = repo.load_hotel(settings.HOTEL_NAME)
        chat_history = repo.get_chat_history(user_id)

    response, _ = run_hotel_agent(
        hotel=hotel,
        user_message="Show me all room information",
        chat_history=chat_history
    )

    # Save to DB
    with SessionLocal() as db:
        repo = HotelRepository(db)
        session = repo.get_or_create_session(user_id)
        repo.save_message(session.id, "user", "Show me all room information")
        repo.save_message(session.id, "assistant", response)

    await update.message.reply_text(response)


async def reservations_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reservations command - show all reservations."""
    user_id = str(update.effective_user.id)

    with SessionLocal() as db:
        repo = HotelRepository(db)
        hotel = repo.load_hotel(settings.HOTEL_NAME)
        chat_history = repo.get_chat_history(user_id)

    response, _ = run_hotel_agent(
        hotel=hotel,
        user_message="Show me all current reservations",
        chat_history=chat_history
    )

    # Save to DB
    with SessionLocal() as db:
        repo = HotelRepository(db)
        session = repo.get_or_create_session(user_id)
        repo.save_message(session.id, "user", "Show me all current reservations")
        repo.save_message(session.id, "assistant", response)

    await update.message.reply_text(response)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command - clear chat history."""
    user_id = str(update.effective_user.id)
    
    with SessionLocal() as db:
        repo = HotelRepository(db)
        repo.clear_chat_history(user_id)
    
    await update.message.reply_text(
        "🗑️ Conversation history cleared. Starting fresh!\n"
        "How can I help you today?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages."""
    user_id = str(update.effective_user.id)
    user_message = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        with SessionLocal() as db:
            repo = HotelRepository(db)

            # Load hotel from DB (persistent!)
            hotel = repo.load_hotel(settings.HOTEL_NAME)

            # Get chat history from DB (persistent!)
            chat_history = repo.get_chat_history(user_id)

            # Run agent
            response, updated_history = run_hotel_agent(
                hotel=hotel,
                user_message=user_message,
                chat_history=chat_history
            )

            # Save messages to DB
            session = repo.get_or_create_session(user_id)
            repo.save_message(session.id, "user", user_message)
            repo.save_message(session.id, "assistant", response)

            # Save any new reservations to DB
            for reservation in hotel.reservations:
                existing = db.query(ReservationDB).filter(
                    ReservationDB.id == reservation.reservation_id
                ).first()
                if not existing:
                    repo.create_reservation(reservation)

        await _send_long_message(update, response)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Error. Please try again.")


async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


async def _send_long_message(update: Update, text: str, max_length: int = 4096):
    """Split and send long messages (Telegram limit is 4096 chars)."""
    if len(text) <= max_length:
        await update.message.reply_text(text)
        return

    # Split at newlines to avoid breaking words
    parts = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_length:
            parts.append(current)
            current = line
        else:
            current += "\n" + line if current else line

    if current:
        parts.append(current)

    for part in parts:
        await update.message.reply_text(part)


def main():
    """Start the Telegram bot."""
    token = settings.TELEGRAM_BOT_TOKEN

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables!")

    # Load hotel to display info
    with SessionLocal() as db:
        repo = HotelRepository(db)
        hotel = repo.load_hotel(settings.HOTEL_NAME)

    print(f"🤖 Starting {hotel.name} Telegram Bot...")
    print(f"🏨 Hotel: {hotel.name} | Rooms: {len(hotel.rooms)}")
    print("✅ Bot is running! Press Ctrl+C to stop.\n")

    # Build application
    app = Application.builder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rooms", rooms_command))
    app.add_handler(CommandHandler("reservations", reservations_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(handle_error)

    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()