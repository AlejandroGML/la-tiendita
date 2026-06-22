"""Integration tests for wishlist — real DB, no mocks."""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.services.wishlist_service import WishlistService

@pytest.mark.asyncio
async def test_add_and_list_wishlist(session: AsyncSession):
    """Add items and verify they appear in wishlist."""
    user_id = uuid4()
    email = f"wl-{uuid4().hex[:8]}@test.com"
    await session.execute(text("INSERT INTO users (id, email, password_hash, name, role, preferred_lang, is_verified, created_at, updated_at) VALUES (:id, :email, 'hash', 'Test', 'customer', 'es', true, now(), now())").bindparams(id=user_id, email=email))
    
    # Create products with unique slugs
    p1 = uuid4(); p2 = uuid4()
    await session.execute(text(f"INSERT INTO products (id, slug, price, source_dataset, created_at, updated_at) VALUES (:p1, 'test-wl-{p1.hex[:6]}', 10.00, 'test', now(), now())").bindparams(p1=p1))
    await session.execute(text(f"INSERT INTO products (id, slug, price, source_dataset, created_at, updated_at) VALUES (:p2, 'test-wl-{p2.hex[:6]}', 20.00, 'test', now(), now())").bindparams(p2=p2))

    svc = WishlistService()
    await svc.add_item(session, user_id, p1)
    await svc.add_item(session, user_id, p2)
    
    wishlist = await svc.get_wishlist(session, user_id)
    assert len(wishlist.items) == 2

@pytest.mark.asyncio
async def test_remove_item(session: AsyncSession):
    """Remove an item from wishlist."""
    user_id = uuid4()
    email = f"wlr-{uuid4().hex[:8]}@test.com"
    await session.execute(text("INSERT INTO users (id, email, password_hash, name, role, preferred_lang, is_verified, created_at, updated_at) VALUES (:id, :email, 'hash', 'T', 'customer', 'es', true, now(), now())").bindparams(id=user_id, email=email))
    pid = uuid4()
    await session.execute(text(f"INSERT INTO products (id, slug, price, source_dataset, created_at, updated_at) VALUES (:pid, 'test-wl-r-{pid.hex[:6]}', 15.00, 'test', now(), now())").bindparams(pid=pid))

    svc = WishlistService()
    await svc.add_item(session, user_id, pid)
    await svc.remove_item(session, user_id, pid)
    
    wishlist = await svc.get_wishlist(session, user_id)
    assert len(wishlist.items) == 0
