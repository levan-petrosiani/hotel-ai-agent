from langchain_core.tools import tool
from models import Hotel
from datetime import date

def _calculate_nights(check_in: str, check_out: str) -> int:
    """Helper to calculate number of nights"""
    ci_day, ci_month, ci_year = map(int, check_in.split("/"))
    co_day, co_month, co_year = map(int, check_out.split("/"))
    ci = date(ci_year, ci_month, ci_day)
    co = date(co_year, co_month, co_day)
    return (co - ci).days

@tool
def get_available_rooms(check_in: str, check_out: str, num_guests: int, hotel: Hotel) -> str:
    
    """
    Check which rooms are available for given dates and number of guests.
    
    Args:
        check_in: Check-in date in format 'DD/MM/YYYY'
        check_out: Check-out date in format 'DD/MM/YYYY'
        num_guests: Number of guests
        hotel: Hotel instance
    
    Returns:
        String describing available rooms with prices
    """
    available = hotel.find_available_rooms(check_in, check_out, num_guests)
    
    if not available:
        return f"No rooms available for {num_guests} guests from {check_in} to {check_out}."
    
    nights = _calculate_nights(check_in, check_out)
    
    result = f"Available rooms for {num_guests} guests ({nights} nights):\\n\\n"
    for room in available:
        # price = room.calculate_price(nights, num_guests)
        
        result += f"Room {room.room_number} ({room.room_type})\\n"
        result += f"  Capacity: {room.capacity} guests\\n"
        result += f"  Base: ${room.base_price}/night\\n"
    
    return result

@tool
def make_reservation_tool(guest_name: str, room_number: str, check_in: str, 
                          check_out: str, num_guests: int, hotel: Hotel,
                          email: str = None, phone: str = None) -> str:
    
    """
    Make a reservation for a guest.
    
    Args:
        guest_name: Full name of the guest
        room_number: Room number (e.g., '101', '201')
        check_in: Check-in date in format 'DD/MM/YYYY'
        check_out: Check-out date in format 'DD/MM/YYYY'
        num_guests: Number of guests
        hotel: Hotel instance
        email: Guest email address (optional)
        phone: Guest phone number (optional)
    
    Returns:
        Confirmation message or error
    """

    if not email or not phone:
        return "❌ Cannot make reservation: Email and phone number are required. Please ask the guest for their contact information."

    reservation = hotel.make_reservation(guest_name, room_number, check_in, check_out, num_guests, email, phone)
    
    if reservation:
        nights = reservation.get_duration()
        cost = reservation.room.calculate_price(nights, num_guests)
        
        result = f"✅ Reservation Confirmed!\\n\\n"
        result += f"Confirmation Number: {reservation.reservation_id}\\n"
        result += f"Guest: {guest_name}\\n"
        if email:
            result += f"Email: {email}\n"
        if phone:
            result += f"Phone: {phone}\n"
        result += f"Room: {room_number} ({reservation.room.room_type})\\n"
        result += f"Check-in: {check_in}\\n"
        result += f"Check-out: {check_out}\\n"
        result += f"Guests: {num_guests}\\n"
        result += f"Duration: {nights} nights\\n"
        result += f"Total Cost: ${cost}\\n"
        return result
    else:
        return f"❌ Unable to make reservation. Room {room_number} may not be available or doesn't have enough capacity."

@tool
def cancel_reservation_tool(reservation_id: int, hotel: Hotel) -> str:
    
    """
    Cancel a reservation by ID.
    
    Args:
        reservation_id: The reservation ID to cancel
        hotel: Hotel instance
    
    Returns:
        Confirmation message
    """
    if hotel.cancel_reservation(reservation_id):
        return f"✅ Reservation {reservation_id} has been cancelled successfully."
    else:
        return f"❌ Reservation {reservation_id} not found."

@tool
def get_all_rooms_info(hotel: Hotel) -> str:
    
    """
    Get information about all rooms in the hotel.
    
    Args:
        hotel: Hotel instance
    
    Returns:
        String with details about all rooms
    """
    
    result = f"🏨 {hotel.name} - Room Information\\n\\n"
    for room in hotel.rooms:
        result += f"Room {room.room_number} - {room.room_type}\\n"
        result += f"  Base Price: ${room.base_price}/night\\n"
        result += f"  Capacity: {room.capacity} guests\\n\\n"
    
    result += f"  Extra guest fee: $25/guest/night (over 2 guests)\\n"
    return result

@tool
def get_current_reservations(hotel: Hotel) -> str:
    """
    Get a list of all current reservations.
    
    Args:
        hotel: Hotel instance
    
    Returns:
        String with all reservation details
    """
    if not hotel.reservations:
        return "No current reservations."
    
    result = f"📋 Current Reservations ({len(hotel.reservations)} total):\\n\\n"
    for res in hotel.reservations:
        result += f"ID: {res.reservation_id}\\n"
        result += f"  Guest: {res.guest_name}\\n"
        if res.email:
            result += f"  Email: {res.email}\n"
        if res.phone:
            result += f"  Phone: {res.phone}\n"
        result += f"  Room: {res.room.room_number} ({res.room.room_type})\\n"
        result += f"  Dates: {res.check_in} to {res.check_out}\\n"
        result += f"  Guests: {res.num_guests}\\n\\n"
    return result