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
from database.models import ReservationDB, HITLSessionDB

from agents.hitl_detector import detect_hitl_need
import asyncio

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global bot instance
bot_instance = None

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


async def notify_staff(guest_id: str, guest_name: str, message: str, 
                      reason: str, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send alert to staff Telegram."""
    staff_id = settings.STAFF_TELEGRAM_ID
    
    reason_text = {
        "discount_request": "💰 Discount/Deal Request",
        "manual_escalation": "👤 Guest Requested Human",
        "complaint": "😟 Complaint Detected",
        "agent_uncertainty": "❓ Agent Uncertain"
    }.get(reason, "ℹ️ Needs Assistance")
    
    alert = (
        f"🚨 {reason_text}\n\n"
        f"Guest: {guest_name}\n"
        f"ID: {guest_id}\n"  
        f"Message: \"{message}\"\n\n"
        f"👉 Reply to this message to respond to the guest."
    )
    
    sent_msg = await context.bot.send_message(
        chat_id=staff_id,
        text=alert,
    )
    
    return sent_msg.message_id


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages."""
    user_id = str(update.effective_user.id)
    user_message = update.message.text
    
    # Check if this is staff replying to a guest
    if user_id == str(settings.STAFF_TELEGRAM_ID):
        if update.message.reply_to_message:
            await handle_staff_reply(update, context)
            return
    
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        with SessionLocal() as db:
            repo = HotelRepository(db)
            
            # Check if guest is waiting for staff
            pending_hitl = repo.get_pending_hitl_session(user_id)
            if pending_hitl:
                await update.message.reply_text(
                    "⏳ Our team is reviewing your request. "
                    "You'll receive a response shortly!"
                )
                return
            
            # Load hotel and chat history
            hotel = repo.load_hotel(settings.HOTEL_NAME)
            chat_history = repo.get_chat_history(user_id)
            
            # Detect HITL before running agent
            needs_human, reason = detect_hitl_need(user_message)
            
            if needs_human:
                # Create HITL session
                staff_msg_id = await notify_staff(
                    guest_id=user_id,
                    guest_name=update.effective_user.first_name,
                    message=user_message,
                    reason=reason,
                    context=context
                )
                
                repo.create_hitl_session(
                    guest_user_id=user_id,
                    guest_message=user_message,
                    reason=reason,
                    staff_msg_id=staff_msg_id
                )
                
                # Send holding message to guest
                await update.message.reply_text(
                    "👤 I've forwarded your request to our team. "
                    "They'll respond to you shortly!"
                )
                
                # Schedule timeout check
                asyncio.create_task(
                    check_hitl_timeout(user_id, context, 5)
                )
                return
            
            # Normal agent flow
            response, updated_history = run_hotel_agent(
                hotel=hotel,
                user_message=user_message,
                chat_history=chat_history
            )
            
            # Save to DB
            session = repo.get_or_create_session(user_id)
            repo.save_message(session.id, "user", user_message)
            repo.save_message(session.id, "assistant", response)
            
            # Save reservations
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


async def handle_staff_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle staff replying to guest via Telegram."""
    alert_text = update.message.reply_to_message.text
    
    import re
    # Match plain format: ID: 6330450293
    match = re.search(r'ID:\s*(\d+)', alert_text)
    
    if not match:
        await update.message.reply_text(f"❌ Could not find guest ID\n\nDebug:\n{alert_text}")
        return
    
    guest_id = match.group(1)
    staff_response = update.message.text
    
    # Resolve HITL session in DB
    with SessionLocal() as db:
        repo = HotelRepository(db)
        hitl_session = repo.get_pending_hitl_session(guest_id)
        
        if hitl_session:
            repo.resolve_hitl_session(hitl_session.id, staff_response)
    
    # Forward to guest
    try:
        await context.bot.send_message(
            chat_id=guest_id,
            text=f"👤 Staff Response:\n\n{staff_response}"  # Remove Markdown
        )
        
        await update.message.reply_text("✅ Response sent to guest!")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send: {e}")


async def check_hitl_timeout(guest_id: str, context: ContextTypes.DEFAULT_TYPE, 
                            minutes: int = 5):
    """Check if HITL session timed out and notify guest."""
    await asyncio.sleep(minutes * 60)
    
    with SessionLocal() as db:
        repo = HotelRepository(db)
        hitl_session = repo.get_pending_hitl_session(guest_id)
        
        if hitl_session and hitl_session.status == "pending":
            # Still pending after timeout
            hitl_session.status = "timeout"
            db.commit()
            
            await context.bot.send_message(
                chat_id=guest_id,
                text=(
                    "⏰ Our team is taking a bit longer than expected. "
                    "We'll get back to you as soon as possible!\n\n"
                    "In the meantime, feel free to ask me other questions!"
                )
            )


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