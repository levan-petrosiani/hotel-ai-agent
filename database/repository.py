from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from .models import RoomDB, GuestDB, ReservationDB, ChatSessionDB, ChatMessageDB, HITLSessionDB
from models import Hotel, Room, Reservation
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime, timedelta

class HotelRepository:
    """All database operations for the hotel system."""

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # Room operations
    # -------------------------------------------------------------------------

    def add_room(self, room: Room) -> RoomDB:
        """Save a room to the database."""
        db_room = RoomDB(
            room_number=room.room_number,
            room_type=room.room_type,
            base_price=room.base_price,
            capacity=room.capacity
        )
        self.db.add(db_room)
        self.db.commit()
        self.db.refresh(db_room)
        return db_room

    def get_all_rooms(self) -> list[RoomDB]:
        """Get all rooms from the database."""
        return self.db.query(RoomDB).all()

    def get_room_by_number(self, room_number: str) -> Optional[RoomDB]:
        """Get a room by room number."""
        return self.db.query(RoomDB).filter(
            RoomDB.room_number == room_number
        ).first()

    # -------------------------------------------------------------------------
    # Guest operations
    # -------------------------------------------------------------------------

    def get_or_create_guest(
        self, name: str, email: str, phone: str
    ) -> GuestDB:
        """Get existing guest by email or create new one."""
        guest = self.db.query(GuestDB).filter(
            GuestDB.email == email
        ).first()

        if not guest:
            guest = GuestDB(name=name, email=email, phone=phone)
            self.db.add(guest)
            self.db.commit()
            self.db.refresh(guest)

        return guest

    # -------------------------------------------------------------------------
    # Reservation operations
    # -------------------------------------------------------------------------

    def create_reservation(self, reservation: Reservation) -> ReservationDB:
        """Save a reservation to the database."""
        # Get or create guest
        guest = self.get_or_create_guest(
            name=reservation.guest_name,
            email=reservation.email,
            phone=reservation.phone
        )

        # Get room
        db_room = self.get_room_by_number(reservation.room.room_number)

        # Calculate cost
        nights = reservation.get_duration()
        cost = reservation.room.calculate_price(nights, reservation.num_guests)

        db_reservation = ReservationDB(
            room_id=db_room.id,
            guest_id=guest.id,
            check_in=reservation.check_in,
            check_out=reservation.check_out,
            num_guests=reservation.num_guests,
            total_cost=cost,
            status="confirmed"
        )

        self.db.add(db_reservation)
        self.db.commit()
        self.db.refresh(db_reservation)
        return db_reservation

    def cancel_reservation(self, reservation_id: int) -> bool:
        """Cancel a reservation (soft delete - keep record)."""
        reservation = self.db.query(ReservationDB).filter(
            ReservationDB.id == reservation_id
        ).first()

        if not reservation:
            return False

        reservation.status = "cancelled"
        self.db.commit()
        return True

    def get_all_reservations(self) -> list[ReservationDB]:
        """Get all active reservations."""
        return self.db.query(ReservationDB).filter(
            ReservationDB.status == "confirmed"
        ).all()

    # -------------------------------------------------------------------------
    # Hotel loading
    # -------------------------------------------------------------------------

    def load_hotel(self, hotel_name: str) -> Hotel:
        """Load hotel with all rooms and reservations from DB."""
        hotel = Hotel(hotel_name)

        # Load rooms
        db_rooms = self.get_all_rooms()
        for db_room in db_rooms:
            room = Room(
                room_number=db_room.room_number,
                room_type=db_room.room_type,
                base_price=db_room.base_price,
                capacity=db_room.capacity
            )
            hotel.add_room(room)

        # Load active reservations
        db_reservations = self.get_all_reservations()
        for db_res in db_reservations:
            room = next(
                r for r in hotel.rooms
                if r.room_number == db_res.room.room_number
            )
            reservation = Reservation(
                reservation_id=db_res.id,
                room=room,
                guest_name=db_res.guest.name,
                check_in=db_res.check_in,
                check_out=db_res.check_out,
                num_guests=db_res.num_guests,
                email=db_res.guest.email,
                phone=db_res.guest.phone
            )
            hotel.reservations.append(reservation)
            hotel.next_reservation_id = max(
                hotel.next_reservation_id,
                db_res.id + 1
            )

        return hotel

    # -------------------------------------------------------------------------
    # Chat session operations
    # -------------------------------------------------------------------------

    def get_or_create_session(
        self, user_id: str, platform: str = "telegram"
    ) -> ChatSessionDB:
        """Get or create a chat session for a user."""
        session = self.db.query(ChatSessionDB).filter(
            ChatSessionDB.user_id == user_id,
            ChatSessionDB.platform == platform
        ).first()

        if not session:
            session = ChatSessionDB(user_id=user_id, platform=platform)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

        return session

    def save_message(
        self, session_id: int, role: str, content: str
    ) -> ChatMessageDB:
        """Save a chat message."""
        message = ChatMessageDB(
            session_id=session_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        return message

    def get_chat_history(self, user_id: str, platform: str = "telegram") -> list:
        """Get chat history as LangChain messages."""
        session = self.get_or_create_session(user_id, platform)

        messages = []
        for msg in session.messages[-20:]:  # Last 20 messages
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        return messages

    def clear_chat_history(self, user_id: str, platform: str = "telegram"):
        """Clear chat history for a user."""
        session = self.get_or_create_session(user_id, platform)
        self.db.query(ChatMessageDB).filter(
            ChatMessageDB.session_id == session.id
        ).delete()
        self.db.commit()

    # -------------------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------------------

    def get_revenue_report(self) -> dict:
        """Get revenue analytics from DB."""
        reservations = self.get_all_reservations()

        total_revenue = sum(
            r.total_cost for r in reservations
            if r.total_cost is not None
        )

        return {
            "total_revenue": round(total_revenue, 2),
            "num_reservations": len(reservations),
            "average_per_reservation": round(
                total_revenue / len(reservations), 2
            ) if reservations else 0.0
        }
    

    def create_hitl_session(self, guest_user_id: str, guest_message: str, 
                       reason: str, staff_msg_id: int) -> HITLSessionDB:
        """Create a new HITL session."""
        session = HITLSessionDB(
            guest_user_id=guest_user_id,
            guest_message=guest_message,
            reason=reason,
            staff_alert_msg_id=staff_msg_id,
            status="pending"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_pending_hitl_session(self, guest_user_id: str) -> Optional[HITLSessionDB]:
        """Get pending HITL session for a guest."""
        return self.db.query(HITLSessionDB).filter(
            HITLSessionDB.guest_user_id == guest_user_id,
            HITLSessionDB.status == "pending"
        ).first()

    def resolve_hitl_session(self, session_id: int, staff_response: str):
        """Mark HITL session as resolved."""
        session = self.db.query(HITLSessionDB).filter(
            HITLSessionDB.id == session_id
        ).first()
        
        if session:
            session.status = "resolved"
            session.resolved_at = datetime.now()
            session.staff_response = staff_response
            self.db.commit()

    def timeout_old_sessions(self, minutes: int = 5):
        """Mark old pending sessions as timeout."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        self.db.query(HITLSessionDB).filter(
            HITLSessionDB.status == "pending",
            HITLSessionDB.created_at < cutoff
        ).update({"status": "timeout"})
        self.db.commit()

