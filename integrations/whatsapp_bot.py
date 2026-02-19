from twilio.rest import Client
from agents.hotel_agent import run_hotel_agent
from models import Hotel
import os

# Setup Twilio
client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Simple in-memory chat history (good enough for now!)
chat_sessions = {}

def handle_incoming_whatsapp(request):
    """Handle incoming WhatsApp message"""
    from_number = request.form['From']
    message = request.form['Body']
    
    # Get or create chat history
    if from_number not in chat_sessions:
        chat_sessions[from_number] = []
    
    # Run agent (using your in-memory hotel)
    hotel = initialize_hotel("Demo Hotel")
    response, updated_history = run_hotel_agent(
        hotel=hotel,
        user_message=message,
        chat_history=chat_sessions[from_number]
    )
    
    # Update history
    chat_sessions[from_number] = updated_history
    
    # Send response
    client.messages.create(
        from_='whatsapp:+14155238886',  # Twilio sandbox
        body=response,
        to=from_number
    )
    
    return "OK"