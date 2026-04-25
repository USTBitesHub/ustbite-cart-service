"""create_cart_items_table

Revision ID: 1a2b3c4d5e6f
Revises:
Create Date: 2026-04-25 00:00:00
"""
from alembic import op

revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # asyncpg requires ONE statement per op.execute() call

    op.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            menu_item_id UUID NOT NULL,
            restaurant_id UUID NOT NULL,
            restaurant_name VARCHAR NOT NULL,
            item_name VARCHAR NOT NULL,
            item_description VARCHAR,
            item_price NUMERIC(10,2) NOT NULL,
            item_image VARCHAR,
            item_veg BOOLEAN DEFAULT TRUE,
            item_category VARCHAR,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            CONSTRAINT uq_cart_user_menuitem UNIQUE (user_id, menu_item_id)
        )
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_cart_items_user_id ON cart_items(user_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cart_items CASCADE")
