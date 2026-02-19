from models import Hotel
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Annotated, TypedDict, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from config.settings import settings

# Import tools (will be wrapped with hotel instance)
from .tools import (
    get_available_rooms,
    make_reservation_tool,
    cancel_reservation_tool,
    get_all_rooms_info,
    get_current_reservations
)

class HotelState(TypedDict):
    """State for the hotel reservation agent."""
    messages: Annotated[list[BaseMessage], add_messages]
    hotel: Hotel
    guest_name: str | None
    email: str | None
    phone: str | None
    room_number: str | None
    check_in: str | None
    check_out: str | None
    num_guests: int | None
    available_rooms: list | None
    reservation_confirmed: bool

def create_hotel_tools(hotel: Hotel):
    """Create hotel-specific tools bound to a hotel instance."""
    
    @tool
    def check_availability(check_in: str, check_out: str, num_guests: int) -> str:
        """
        Check which rooms are available for given dates and number of guests.
        
        Args:
            check_in: Check-in date in format DD/MM/YYYY
            check_out: Check-out date in format DD/MM/YYYY  
            num_guests: Number of guests
        """
        return get_available_rooms.invoke({
            "check_in": check_in,
            "check_out": check_out,
            "num_guests": num_guests,
            "hotel": hotel
        })
    
    @tool
    def book_room(guest_name: str, room_number: str, check_in: str, 
                  check_out: str, num_guests: int, email: str, phone: str) -> str:
        """
        Make a hotel reservation. All fields are required.
        
        Args:
            guest_name: Full name of guest
            room_number: Room number (e.g., '101', '201')
            check_in: Check-in date DD/MM/YYYY
            check_out: Check-out date DD/MM/YYYY
            num_guests: Number of guests
            email: Guest email address
            phone: Guest phone number
        """
        return make_reservation_tool.invoke({
            "guest_name": guest_name,
            "room_number": room_number,
            "check_in": check_in,
            "check_out": check_out,
            "num_guests": num_guests,
            "email": email,
            "phone": phone,
            "hotel": hotel
        })
    
    @tool
    def cancel_booking(reservation_id: int) -> str:
        """
        Cancel a reservation by ID.
        
        Args:
            reservation_id: The reservation ID to cancel
        """
        return cancel_reservation_tool.invoke({
            "reservation_id": reservation_id,
            "hotel": hotel
        })
    
    @tool
    def get_room_info() -> str:
        """Get information about all available room types."""
        return get_all_rooms_info.invoke({"hotel": hotel})
    
    @tool
    def view_reservations() -> str:
        """View all current reservations."""
        return get_current_reservations.invoke({"hotel": hotel})
    
    return [check_availability, book_room, cancel_booking, get_room_info, view_reservations]

def create_hotel_agent(hotel: Hotel):
    """Create a LangGraph-based hotel agent."""
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME,
        google_api_key=settings.API_KEY,
        temperature=0.1,
    )
    
    # Create hotel-specific tools
    tools = create_hotel_tools(hotel)
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # System message
    system_message = SystemMessage(content=f"""You are a helpful reservation assistant for {hotel.name}.
    CRITICAL RULES:
    1. To make a reservation, you MUST call the book_room tool
    2. NEVER say "Reservation Confirmed" without seeing a confirmation from the tool
    3. Before calling book_room, you MUST have ALL of these: guest_name, room_number, check_in, check_out, num_guests, email, phone
    4. If missing ANY information, ASK the user for it - DO NOT proceed
    5. DO NOT invent or hallucinate email addresses or phone numbers
    6. Date format must be DD/MM/YYYY (e.g., 15/03/2026)
    7. Use ONLY language initiated by the user

    Available rooms:
    - Rooms 101, 102 (Standard): 2 guests max
    - Room 201 (Deluxe): 4 guests max
    - Room 301 (Suite): 6 guests max

    Extra guests: ${settings.EXTRA_GUEST_FEE}/night each (over {settings.BASE_GUEST_COUNT} guests)

    Your job is to help guests check availability, make reservations, cancel bookings, and answer questions.
    Always be friendly and professional.

    When you need to use a tool, just call it directly. The system will handle the rest."""
    )

    # Agent node - decides what to do
    def agent_node(state: HotelState) -> HotelState:
        """Main agent that decides which tool to call."""
        messages = [system_message] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Should continue decision
    def should_continue(state: HotelState) -> Literal["tools", "end"]:
        """Determine if we should continue to tools or end."""
        last_message = state["messages"][-1]
        
        # If LLM makes a tool call, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # Otherwise end
        return "end"
    
    # Build the graph
    workflow = StateGraph(HotelState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # After tools, always go back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    app = workflow.compile()
    
    return app

# def run_hotel_agent(hotel: Hotel, user_message: str, chat_history: list = None):
#     """
#     Run the hotel agent with a user message.
    
#     Args:
#         hotel: Hotel instance
#         user_message: User's message
#         chat_history: Previous conversation messages
        
#     Returns:
#         Agent's response and updated chat history
#     """
#     app = create_hotel_agent(hotel)
    
#     # Initialize state
#     messages = chat_history if chat_history else []
#     messages.append(HumanMessage(content=user_message))
    
#     state = {
#         "messages": messages,
#         "hotel": hotel,
#         "guest_name": None,
#         "email": None,
#         "phone": None,
#         "room_number": None,
#         "check_in": None,
#         "check_out": None,
#         "num_guests": None,
#         "available_rooms": None,
#         "reservation_confirmed": False
#     }
    
#     # Run the agent
#     result = app.invoke(state)
    
#     # Get the last AI message
#     ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
#     last_response = ai_messages[-1].content if ai_messages else "I apologize, I couldn't process that."
    
#     return last_response, result["messages"]

def run_hotel_agent(hotel: Hotel, user_message: str, chat_history: list = None):
    app = create_hotel_agent(hotel)
    
    messages = chat_history if chat_history else []
    messages.append(HumanMessage(content=user_message))
    
    state = {
        "messages": messages,
        "hotel": hotel,
        "guest_name": None,
        "email": None,
        "phone": None,
        "room_number": None,
        "check_in": None,
        "check_out": None,
        "num_guests": None,
        "available_rooms": None,
        "reservation_confirmed": False
    }
    
    result = app.invoke(state)
    
    # Get the last AI message
    ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
    last_message = ai_messages[-1] if ai_messages else None
    
    if last_message is None:
        return "I apologize, I couldn't process that.", result["messages"]
    
    # Handle Gemini's content format (list of blocks vs plain string)
    content = last_message.content
    if isinstance(content, list):
        # Extract text from content blocks
        last_response = " ".join(
            block["text"] 
            for block in content 
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        last_response = content
    
    return last_response, result["messages"]