import uuid
from sqlalchemy import Column, String, Boolean, Numeric, Integer, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Menu item snapshot — stored at time of adding to cart
    # so price/name changes don't silently affect the user's cart
    menu_item_id = Column(UUID(as_uuid=True), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    restaurant_name = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    item_description = Column(String)
    item_price = Column(Numeric(10, 2), nullable=False)
    item_image = Column(String)
    item_veg = Column(Boolean, default=True)
    item_category = Column(String)

    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # One entry per (user, menu_item) — duplicate adds just increment qty
    __table_args__ = (
        UniqueConstraint('user_id', 'menu_item_id', name='uq_cart_user_menuitem'),
    )
