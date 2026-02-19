from datetime import date
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .room import Room

class Reservation:
    """Represents a hotel reservation"""
    
    def __init__(self, reservation_id: int, room: 'Room', guest_name: str,
                 check_in: str, check_out: str, num_guests: int,
                 email: Optional[str] = None, phone: Optional[str] = None):
        self.reservation_id = reservation_id
        self.room = room
        self.guest_name = guest_name
        self.check_in = check_in  # DD/MM/YYYY
        self.check_out = check_out
        self.num_guests = num_guests
        self.email = email
        self.phone = phone

    def get_duration(self) -> int:
        """Calculate stay duration in nights."""
        ci_day, ci_month, ci_year = map(int, self.check_in.split("/"))
        co_day, co_month, co_year = map(int, self.check_out.split("/"))

        ci = date(ci_year, ci_month, ci_day)
        co = date(co_year, co_month, co_day)

        return (co - ci).days
    
    def overlaps_with(self, other: 'Reservation') -> bool:
        """Check if this reservation overlaps with another."""
        ci1_day, ci1_month, ci1_year = map(int, self.check_in.split("/"))
        co1_day, co1_month, co1_year = map(int, self.check_out.split("/"))
        ci2_day, ci2_month, ci2_year = map(int, other.check_in.split("/"))
        co2_day, co2_month, co2_year = map(int, other.check_out.split("/"))
        
        ci1 = date(ci1_year, ci1_month, ci1_day)
        co1 = date(co1_year, co1_month, co1_day)
        ci2 = date(ci2_year, ci2_month, ci2_day)
        co2 = date(co2_year, co2_month, co2_day)
        
        # Check for overlap
        if co1 <= ci2:
            return False
        if co2 <= ci1:
            return False
        return True

    def calculate_total_cost(self) -> float:
        """Calculate total cost for this reservation."""
        num_nights = self.get_duration()
        return self.room.calculate_price(num_nights, self.num_guests)

    def get_info(self) -> dict:
        """Get reservation information as a dictionary."""
        return {
            "reservation_id": self.reservation_id,
            "room_number": self.room.room_number,
            "guest_name": self.guest_name,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "num_guests": self.num_guests,
            "duration": self.get_duration(),
            "email": self.email,
            "phone": self.phone
        }

    def __str__(self) -> str:
        return (f"Reservation #{self.reservation_id}: {self.guest_name} - "
                f"Room {self.room.room_number} ({self.check_in} to {self.check_out})")