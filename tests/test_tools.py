import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import Hotel, Room
from agents.tools import (
    get_available_rooms,
    make_reservation_tool,
    cancel_reservation_tool,
    get_all_rooms_info,
    get_current_reservations
)

@pytest.fixture
def sample_hotel():
    """Create a sample hotel for testing."""
    hotel = Hotel("Test Hotel")
    hotel.add_room(Room("101", "Standard", 100, 2))
    hotel.add_room(Room("102", "Standard", 100, 2))
    hotel.add_room(Room("201", "Deluxe", 150, 4))
    hotel.add_room(Room("301", "Suite", 250, 6))
    return hotel

def test_get_available_rooms_tool(sample_hotel):
    """Test the get_available_rooms tool."""
    result = get_available_rooms.invoke({
        "check_in": "10/03/2026",
        "check_out": "15/03/2026",
        "num_guests": 2,
        "hotel": sample_hotel
    })
    
    assert "Room 101" in result
    assert "Room 102" in result
    assert "5 nights" in result

def test_make_reservation_tool_success(sample_hotel):
    """Test successful reservation with tool."""
    result = make_reservation_tool.invoke({
        "guest_name": "John Doe",
        "room_number": "101",
        "check_in": "10/03/2026",
        "check_out": "15/03/2026",
        "num_guests": 2,
        "hotel": sample_hotel,
        "season": "medium"
    })
    
    assert "✅ Reservation Confirmed!" in result
    assert "John Doe" in result
    assert "Confirmation Number: 1" in result
    assert len(sample_hotel.reservations) == 1

def test_make_reservation_tool_failure(sample_hotel):
    """Test failed reservation with tool."""
    # Make first reservation
    make_reservation_tool.invoke({
        "guest_name": "Alice",
        "room_number": "101",
        "check_in": "10/03/2026",
        "check_out": "15/03/2026",
        "num_guests": 2,
        "hotel": sample_hotel,
        "season": "low"
    })
    
    # Try overlapping reservation
    result = make_reservation_tool.invoke({
        "guest_name": "Bob",
        "room_number": "101",
        "check_in": "12/03/2026",
        "check_out": "17/03/2026",
        "num_guests": 2,
        "hotel": sample_hotel,
        "season": "low"
    })
    
    assert "❌ Unable to make reservation" in result
    assert len(sample_hotel.reservations) == 1

def test_cancel_reservation_tool(sample_hotel):
    """Test canceling reservation with tool."""
    # Create reservation
    make_reservation_tool.invoke({
        "guest_name": "John",
        "room_number": "101",
        "check_in": "10/03/2026",
        "check_out": "15/03/2026",
        "num_guests": 2,
        "hotel": sample_hotel
    })
    
    # Cancel it
    result = cancel_reservation_tool.invoke({
        "reservation_id": 1,
        "hotel": sample_hotel
    })
    
    assert "✅" in result
    assert "cancelled successfully" in result
    assert len(sample_hotel.reservations) == 0

def test_get_all_rooms_info_tool(sample_hotel):
    """Test getting all rooms info."""
    result = get_all_rooms_info.invoke({"hotel": sample_hotel})
    
    assert "Test Hotel" in result
    assert "Room 101" in result
    assert "Standard" in result
    assert "$100/night" in result
    assert "Season Multipliers" in result

def test_get_current_reservations_tool_empty(sample_hotel):
    """Test getting reservations when there are none."""
    result = get_current_reservations.invoke({"hotel": sample_hotel})
    assert "No current reservations" in result

def test_get_current_reservations_tool_with_data(sample_hotel):
    """Test getting reservations with data."""
    # Create some reservations
    make_reservation_tool.invoke({
        "guest_name": "Alice",
        "room_number": "101",
        "check_in": "10/03/2026",
        "check_out": "15/03/2026",
        "num_guests": 2,
        "hotel": sample_hotel
    })
    
    make_reservation_tool.invoke({
        "guest_name": "Bob",
        "room_number": "201",
        "check_in": "20/03/2026",
        "check_out": "25/03/2026",
        "num_guests": 3,
        "hotel": sample_hotel
    })
    
    result = get_current_reservations.invoke({"hotel": sample_hotel})
    
    assert "2 total" in result
    assert "Alice" in result
    assert "Bob" in result
    assert "101" in result  # Just check room number
    assert "201" in result
