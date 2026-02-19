from typing import Optional
from config.settings import settings

class Room:
    """Represents a hotel room with pricing and capacity."""
    
    def __init__(self, room_number: str, room_type: str, base_price: float, capacity: int):
        self.room_number = room_number
        self.room_type = room_type
        self.base_price = base_price
        self.capacity = capacity

    def calculate_price(self, num_nights: int, num_guests: int) -> float:
        """
        Calculate total price for a stay.
        
        Args:
            num_nights: Number of nights
            num_guests: Number of guests
            
        Returns:
            Total price, or -1 if capacity exceeded
        """
        if num_guests > self.capacity:
            return -1

        total_price = self.base_price * num_nights

        # Add extra guest fees
        if num_guests > settings.BASE_GUEST_COUNT:
            extra_guests = num_guests - settings.BASE_GUEST_COUNT
            total_price += (extra_guests * settings.EXTRA_GUEST_FEE * num_nights)

        return round(total_price, 2)

    def get_info(self) -> dict:
        """Get room information as a dictionary."""
        return {
            "room_number": self.room_number,
            "room_type": self.room_type,
            "base_price": self.base_price,
            "capacity": self.capacity
        }

    def __str__(self) -> str:
        return f"Room {self.room_number} ({self.room_type}) - ${self.base_price}/night, {self.capacity} guests"
    
    def __repr__(self) -> str:
        return f"Room('{self.room_number}', '{self.room_type}', {self.base_price}, {self.capacity})"