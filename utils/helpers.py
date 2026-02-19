from models import Hotel, Room

def initialize_hotel(name: str = "Paragraph Hotel") -> Hotel:
    """
    Initialize a hotel with default rooms.
    
    Args:
        name: Hotel name
        
    Returns:
        Configured Hotel instance
    """
    hotel = Hotel(name)
    
    # Add default rooms
    hotel.add_room(Room("101", "Standard", 100, 2))
    hotel.add_room(Room("102", "Standard", 100, 2))
    hotel.add_room(Room("201", "Deluxe", 150, 4))
    hotel.add_room(Room("301", "Suite", 250, 6))
    
    return hotel

def format_currency(amount: float) -> str:
    """Format amount as currency string"""
    return f"${amount:,.2f}"