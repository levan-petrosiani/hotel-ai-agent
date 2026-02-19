import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import Room, Reservation, Hotel

def test_room_creation():
    """Test room creation and basic properties."""
    room = Room("101", "Standard", 100, 2)
    assert room.room_number == "101"
    assert room.room_type == "Standard"
    assert room.base_price == 100
    assert room.capacity == 2

def test_room_price_calculation():
    """Test room price calculation with different scenarios."""
    room = Room("101", "Standard", 100, 2)
    
    # Basic pricing
    assert room.calculate_price(3, 2, "low") == 300.0
    
    # Season multipliers
    assert room.calculate_price(2, 2, "medium") == 240.0
    assert room.calculate_price(2, 2, "high") == 300.0
    
    # Exceeds capacity (room capacity is 2, can't fit 3 guests)
    assert room.calculate_price(2, 3, "low") == -1

    # Extra guest fees (need room with higher capacity)
    deluxe_room = Room("201", "Deluxe", 150, 4)
    assert deluxe_room.calculate_price(2, 3, "low") == 350.0  # 300 + 50
    assert deluxe_room.calculate_price(2, 4, "low") == 400.0  # 300 + 100

def test_reservation_creation():
    """Test reservation creation."""
    room = Room("101", "Standard", 100, 2)
    res = Reservation(1, room, "John Doe", "10/03/2026", "15/03/2026", 2)
    
    assert res.reservation_id == 1
    assert res.guest_name == "John Doe"
    assert res.num_guests == 2
    assert res.get_duration() == 5

def test_reservation_overlap():
    "Test reservation overlap detection."
    room = Room("101", "Standard", 100, 2)
    res1 = Reservation(1, room, "Alice", "10/03/2026", "15/03/2026", 2)
    res2 = Reservation(2, room, "Bob", "13/03/2026", "18/03/2026", 2)
    res3 = Reservation(3, room, "Charlie", "15/03/2026", "20/03/2026", 2)
    
    assert res1.overlaps_with(res2) == True  # Overlap
    assert res1.overlaps_with(res3) == False  # No overlap (same day checkout/checkin)
    assert res2.overlaps_with(res3) == True  # Overlap

def test_hotel_add_room():
    "Test adding rooms to hotel."
    hotel = Hotel("Test Hotel")
    room = Room("101", "Standard", 100, 2)
    hotel.add_room(room)
    
    assert len(hotel.rooms) == 1
    assert hotel.rooms[0].room_number == "101"

def test_hotel_find_available_rooms():
    """Test finding available rooms."""
    hotel = Hotel("Test Hotel")
    hotel.add_room(Room("101", "Standard", 100, 2))
    hotel.add_room(Room("201", "Deluxe", 150, 4))
    
    # All rooms available
    available = hotel.find_available_rooms("10/03/2026", "15/03/2026", 2)
    assert len(available) == 2
    
    # Make a reservation
    hotel.make_reservation("Alice", "101", "10/03/2026", "15/03/2026", 2)
    
    # Only one room available now
    available = hotel.find_available_rooms("10/03/2026", "15/03/2026", 2)
    assert len(available) == 1
    assert available[0].room_number == "201"

def test_hotel_make_reservation():
    """Test making reservations."""
    hotel = Hotel("Test Hotel")
    hotel.add_room(Room("101", "Standard", 100, 2))
    
    # Successful reservation
    res = hotel.make_reservation("John Doe", "101", "10/03/2026", "15/03/2026", 2)
    assert res is not None
    assert res.reservation_id == 1
    assert len(hotel.reservations) == 1
    
    # Failed reservation (room occupied)
    res2 = hotel.make_reservation("Jane Doe", "101", "12/03/2026", "17/03/2026", 2)
    assert res2 is None
    assert len(hotel.reservations) == 1

def test_hotel_cancel_reservation():
    """Test canceling reservations."""
    hotel = Hotel("Test Hotel")
    hotel.add_room(Room("101", "Standard", 100, 2))
    
    res = hotel.make_reservation("John Doe", "101", "10/03/2026", "15/03/2026", 2)
    assert len(hotel.reservations) == 1
    
    # Cancel existing reservation
    result = hotel.cancel_reservation(res.reservation_id)
    assert result == True
    assert len(hotel.reservations) == 0
    
    # Try to cancel non-existent reservation
    result = hotel.cancel_reservation(999)
    assert result == False

def test_hotel_revenue_report():
    """Test revenue report generation."""
    hotel = Hotel("Test Hotel")
    hotel.add_room(Room("101", "Standard", 100, 2))
    hotel.add_room(Room("201", "Deluxe", 150, 4))
    
    # No reservations
    report = hotel.get_revenue_report("low")
    assert report["total_revenue"] == 0.0
    assert report["num_reservations"] == 0
    
    # Add reservations
    hotel.make_reservation("Alice", "101", "10/03/2026", "15/03/2026", 2)  # 5 nights * 100 = 500
    hotel.make_reservation("Bob", "201", "10/03/2026", "12/03/2026", 3)    # 2 nights * 150 + 1*25*2 = 350

    report = hotel.get_revenue_report("low")
    assert report["total_revenue"] == 850.0
    assert report["num_reservations"] == 2
    assert report["average_per_reservation"] == 425.0
