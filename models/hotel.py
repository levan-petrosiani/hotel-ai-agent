from typing import List, Optional
from .room import Room
from .reservation import Reservation

class Hotel:
    """Manages hotel rooms and reservations."""
    
    def __init__(self, name: str):
        self.name = name
        self.rooms: List[Room] = []
        self.reservations: List[Reservation] = []
        self.next_reservation_id = 1

    def add_room(self, room: Room) -> None:
        """Add a room to the hotel."""
        self.rooms.append(room)

    def find_available_rooms(self, check_in: str, check_out: str, 
                            num_guests: int) -> List[Room]:
        """
        Find rooms available for the specified dates and guest count.
        
        Args:
            check_in: Check-in date (DD/MM/YYYY)
            check_out: Check-out date (DD/MM/YYYY)
            num_guests: Number of guests
            
        Returns:
            List of available rooms
        """
        available = []

        for room in self.rooms:
            if room.capacity < num_guests:
                continue

            # Check if room is available (no overlapping reservations)
            is_available = True
            for reservation in self.reservations:
                if reservation.room.room_number == room.room_number:
                    temp_res = Reservation(0, room, "", check_in, check_out, num_guests)
                    if reservation.overlaps_with(temp_res):
                        is_available = False
                        break
            
            if is_available:
                available.append(room)
        
        return available

    def make_reservation(self, guest_name: str, room_number: str, 
                        check_in: str, check_out: str, 
                        num_guests: int, email: Optional[str] = None,
                        phone: Optional[str] = None) -> Optional[Reservation]:
        """
        Create a new reservation.
        
        Returns:
            Reservation object if successful, None otherwise
        """
        # Find room
        room = next((r for r in self.rooms if r.room_number == room_number), None)
        if room is None:
            return None
        
        # Check availability
        available_rooms = self.find_available_rooms(check_in, check_out, num_guests)
        if room not in available_rooms:
            return None
        
        # Check capacity
        if room.capacity < num_guests:
            return None
        
        # Create reservation
        reservation = Reservation(
            self.next_reservation_id,
            room,
            guest_name,
            check_in,
            check_out,
            num_guests,
            email,
            phone
        )

        self.reservations.append(reservation)
        self.next_reservation_id += 1

        return reservation

    def cancel_reservation(self, reservation_id: int) -> bool:
        """
        Cancel a reservation by ID.
        
        Returns:
            True if cancelled, False if not found
        """
        for i, reservation in enumerate(self.reservations):
            if reservation.reservation_id == reservation_id:
                self.reservations.pop(i)
                return True
        return False

    def get_revenue_report(self) -> dict:
        """Generate revenue report for all reservations."""
        if not self.reservations:
            return {
                "total_revenue": 0.0,
                "num_reservations": 0,
                "average_per_reservation": 0.0
            }
        
        total = sum(
            res.calculate_total_cost() 
            for res in self.reservations
                if res.calculate_total_cost() != -1
        )
        num_res = len(self.reservations)
        avg = total / num_res if num_res > 0 else 0

        return {
            "total_revenue": round(total, 2),
            "num_reservations": num_res,
            "average_per_reservation": round(avg, 2)
        }

    def get_all_reservations(self) -> List[dict]:
        """Get all reservations as a list of dictionaries."""
        return [res.get_info() for res in self.reservations]