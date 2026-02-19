import streamlit as st
import sys
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from agents.hotel_agent import run_hotel_agent
st.write(f"DEBUG: Using agent from: {run_hotel_agent.__module__}")

from utils import initialize_hotel

# Validate settings
# try:
#     settings.validate()
# except ValueError as e:
#     st.error(f"Configuration Error: {e}")
#     st.info("Please set ANTHROPIC_API_KEY in your .env file")
#     st.stop()

# Initialize hotel in session state
if 'hotel' not in st.session_state:
    st.session_state.hotel = initialize_hotel(settings.HOTEL_NAME)

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Page configuration
st.set_page_config(
    page_title=f"{settings.HOTEL_NAME} AI",
    page_icon="🏨",
    layout="wide"
)

# Main title
st.title(f"🏨 {settings.HOTEL_NAME} AI Assistant")
st.markdown("*Your intelligent concierge powered by LangChain & Ollama*")

# Sidebar
with st.sidebar:
    st.header("📊 Hotel Dashboard")
    
    hotel = st.session_state.hotel
    st.metric("Total Rooms", len(hotel.rooms))
    st.metric("Active Reservations", len(hotel.reservations))
    
    st.divider()
    
    # View reservations
    if st.button("View All Reservations"):
        if hotel.reservations:
            st.write("**Current Reservations:**")
            for res in hotel.reservations:
                with st.expander(f"#{res.reservation_id} - {res.guest_name}"):
                    st.write(f"**Room:** {res.room.room_number} ({res.room.room_type})")
                    st.write(f"**Dates:** {res.check_in} to {res.check_out}")
                    st.write(f"**Guests:** {res.num_guests}")
                    st.write(f"**Duration:** {res.get_duration()} nights")
                    st.write(f"**Email:** {res.email}")
                    st.write(f"**Phone:** {res.phone}")
        else:
            st.info("No active reservations")
    
    st.divider()
    
    # Quick tips
    st.markdown("### Quick Tips")
    st.markdown("""
    Try asking:
    - "What rooms are available?"
    - "Show availability for 2 guests from 15/03/2026 to 20/03/2026"
    - "Book room 201 for John Doe, 2 guests, 10/03/2026 to 15/03/2026, 597 178 811, example@gmail.com"
    - "Cancel reservation 1"
    """)
    
    st.divider()
    
    # Clear chat
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Convert to LangChain messages
                chat_history = []
                for msg in st.session_state.messages[:-1]:
                    if msg["role"] == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    else:
                        chat_history.append(AIMessage(content=msg["content"]))
                
                # Run LangGraph agent (NOT the old create_hotel_agent)
                assistant_message, _ = run_hotel_agent(
                    hotel=st.session_state.hotel,
                    user_message=prompt,
                    chat_history=chat_history
                )
                
                st.markdown(assistant_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
            except Exception as e:
                error_msg = f"I apologize, but I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })