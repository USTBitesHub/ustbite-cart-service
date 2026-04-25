from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from pydantic import BaseModel
from decimal import Decimal
from typing import Any
import uuid

from app.database import get_db
from app.models.models import CartItem
from app.dependencies import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])


# ─── Pydantic schemas (mirror frontend CartItem type) ────────────────────────

class MenuItemSchema(BaseModel):
    id: str
    restaurantId: str
    name: str
    description: str
    price: float
    image: str
    veg: bool
    category: str
    popular: bool | None = None


class CartItemSchema(BaseModel):
    menuItem: MenuItemSchema
    restaurantName: str
    qty: int


class SyncPayload(BaseModel):
    items: list[CartItemSchema]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _to_schema(row: CartItem) -> dict[str, Any]:
    """Convert a DB CartItem row back into the frontend CartItem JSON shape."""
    return {
        "menuItem": {
            "id": str(row.menu_item_id),
            "restaurantId": str(row.restaurant_id),
            "name": row.item_name,
            "description": row.item_description or "",
            "price": float(row.item_price),
            "image": row.item_image or "",
            "veg": row.item_veg,
            "category": row.item_category or "Mains",
        },
        "restaurantName": row.restaurant_name,
        "qty": row.quantity,
    }


def _format_response(data: Any, message: str = "Success") -> dict:
    return {"data": data, "message": message, "status": "success"}


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("")
async def get_cart(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Return all cart items for the logged-in user."""
    user_id = uuid.UUID(user["user_id"])
    result = await db.execute(
        select(CartItem).where(CartItem.user_id == user_id)
    )
    rows = result.scalars().all()
    return _format_response([_to_schema(r) for r in rows])


@router.put("")
async def sync_cart(
    payload: SyncPayload,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Replace the user's entire cart (frontend syncs full state on every change)."""
    user_id = uuid.UUID(user["user_id"])

    # Delete existing cart
    await db.execute(delete(CartItem).where(CartItem.user_id == user_id))

    # Insert new items
    for item in payload.items:
        cart_row = CartItem(
            user_id=user_id,
            menu_item_id=uuid.UUID(item.menuItem.id),
            restaurant_id=uuid.UUID(item.menuItem.restaurantId),
            restaurant_name=item.restaurantName,
            item_name=item.menuItem.name,
            item_description=item.menuItem.description,
            item_price=Decimal(str(item.menuItem.price)),
            item_image=item.menuItem.image,
            item_veg=item.menuItem.veg,
            item_category=item.menuItem.category,
            quantity=item.qty,
        )
        db.add(cart_row)

    await db.commit()
    return _format_response({"ok": True}, "Cart synced")


@router.delete("")
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Clear all items from the user's cart."""
    user_id = uuid.UUID(user["user_id"])
    await db.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await db.commit()
    return _format_response({"ok": True}, "Cart cleared")


@router.post("/items")
async def add_or_update_item(
    item: CartItemSchema,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Add an item or increment quantity if already in cart."""
    user_id = uuid.UUID(user["user_id"])
    menu_item_id = uuid.UUID(item.menuItem.id)

    result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.menu_item_id == menu_item_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.quantity += item.qty
    else:
        db.add(CartItem(
            user_id=user_id,
            menu_item_id=menu_item_id,
            restaurant_id=uuid.UUID(item.menuItem.restaurantId),
            restaurant_name=item.restaurantName,
            item_name=item.menuItem.name,
            item_description=item.menuItem.description,
            item_price=Decimal(str(item.menuItem.price)),
            item_image=item.menuItem.image,
            item_veg=item.menuItem.veg,
            item_category=item.menuItem.category,
            quantity=item.qty,
        ))

    await db.commit()
    # Return updated cart
    result2 = await db.execute(select(CartItem).where(CartItem.user_id == user_id))
    return _format_response([_to_schema(r) for r in result2.scalars().all()], "Item added")


@router.delete("/items/{menu_item_id}")
async def remove_item(
    menu_item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Remove a specific item from the cart."""
    user_id = uuid.UUID(user["user_id"])
    await db.execute(
        delete(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.menu_item_id == uuid.UUID(menu_item_id)
        )
    )
    await db.commit()
    result = await db.execute(select(CartItem).where(CartItem.user_id == user_id))
    return _format_response([_to_schema(r) for r in result.scalars().all()], "Item removed")
