
from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base

class RoomDB(Base):
    """Room table."""
    __tablename__ = "rooms"

    id          = Column(Integer, primary_key=True)
    room_number = Column(String(10), unique=True, nullable=False, index=True)
    room_type   = Column(String(50), nullable=False)
    base_price  = Column(Float, nullable=False)
    capacity    = Column(Integer, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    reservations = relationship("ReservationDB", back_populates="room")

    def __repr__(self):
        return f"<Room {self.room_number} ({self.room_type})>"


class GuestDB(Base):
    """Guest table - reusable across reservations."""
    __tablename__ = "guests"

    id         = Column(Integer, primary_key=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(100), nullable=False, index=True)
    phone      = Column(String(30), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    reservations = relationship("ReservationDB", back_populates="guest")

    def __repr__(self):
        return f"<Guest {self.name} ({self.email})>"


class ReservationDB(Base):
    """Reservation table."""
    __tablename__ = "reservations"

    id         = Column(Integer, primary_key=True)
    room_id    = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    guest_id   = Column(Integer, ForeignKey("guests.id"), nullable=False)
    check_in   = Column(String(10), nullable=False)   # DD/MM/YYYY
    check_out  = Column(String(10), nullable=False)   # DD/MM/YYYY
    num_guests = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=True)
    status     = Column(String(20), default="confirmed")  # confirmed/cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    room  = relationship("RoomDB", back_populates="reservations")
    guest = relationship("GuestDB", back_populates="reservations")

    def __repr__(self):
        return f"<Reservation #{self.id} Room {self.room_id}>"


class ChatSessionDB(Base):
    """Chat session history per Telegram user."""
    __tablename__ = "chat_sessions"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(String(50), nullable=False, index=True)  # Telegram user ID
    platform   = Column(String(20), default="telegram")          # telegram/web/whatsapp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    messages = relationship(
        "ChatMessageDB",
        back_populates="session",
        order_by="ChatMessageDB.created_at"
    )

    def __repr__(self):
        return f"<ChatSession user={self.user_id}>"


class ChatMessageDB(Base):
    """Individual chat messages."""
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role       = Column(String(10), nullable=False)   # "user" or "assistant"
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSessionDB", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.role}: {self.content[:30]}>"
    

class HITLSessionDB(Base):
    """Track human-in-the-loop escalations."""
    __tablename__ = "hitl_sessions"
    
    id = Column(Integer, primary_key=True)
    guest_user_id = Column(String(50), nullable=False, index=True)
    guest_message = Column(Text, nullable=False)
    reason = Column(String(50), nullable=False)  # discount/uncertainty/manual
    staff_alert_msg_id = Column(Integer)  # Telegram message ID sent to staff
    status = Column(String(20), default="pending")  # pending/resolved/timeout
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    staff_response = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<HITLSession guest={self.guest_user_id} status={self.status}>"

