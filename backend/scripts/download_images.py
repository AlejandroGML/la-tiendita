#!/usr/bin/env python3
"""Download fashion images from HuggingFace dataset and assign to products. Batches of 10 for memory safety."""

import asyncio, gc, sys, os, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from app.db.engine import async_session
from app.models.product import Product

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("download_images")
UPLOADS = "/home/alejandro/Proyectos/TiendaVirtual/uploads/products"

async def download():
    from datasets import load_dataset
    from tqdm import tqdm

    # Load streaming dataset
    logger.info("📦 Loading dataset fnauman/fashion-second-hand-front-only-rgb (streaming)...")
    ds = load_dataset("fnauman/fashion-second-hand-front-only-rgb", split="train", streaming=True)
    
    # Get all product IDs
    async with async_session() as session:
        result = await session.execute(select(Product.id, Product.image_urls))
        products = result.all()
    
    logger.info(f"🎯 Products to assign images: {len(products)}")
    
    # Process in batches of 10 for memory safety
    BATCH = 10
    completed = 0
    image_iter = iter(ds)
    product_queue = list(products)
    
    pbar = tqdm(total=len(products), desc="📷 Downloading images", unit="img")
    
    while product_queue:
        batch_products = product_queue[:BATCH]
        product_queue = product_queue[BATCH:]
        updates = []
        
        for product_id, old_urls in batch_products:
            try:
                row = next(image_iter)
                img = row.get("image")
                if img is None:
                    continue
                
                # Save as WebP
                os.makedirs(UPLOADS, exist_ok=True)
                fname = f"{product_id.hex}.webp"
                fpath = os.path.join(UPLOADS, fname)
                
                img.convert("RGB").save(fpath, "WEBP", quality=85)
                updates.append((product_id, f"/uploads/products/{fname}"))
                
                # Free memory
                del row, img
                
            except StopIteration:
                logger.warning("Dataset exhausted before all products got images!")
                break
            except Exception as e:
                logger.warning(f"  ⚠️ Error: {e}")
                continue
        
        # Update DB
        if updates:
            async with async_session() as session:
                for pid, url in updates:
                    await session.execute(
                        Product.__table__.update().where(Product.id == pid).values(image_urls=[url])
                    )
                await session.commit()
        
        completed += len(updates)
        pbar.update(len(updates))
        
        # Force garbage collection every batch
        gc.collect()
        
        if len(product_queue) == 0 or len(updates) < BATCH:
            # Check if dataset exhausted
            try:
                next(image_iter)
            except StopIteration:
                logger.warning("Dataset exhausted!")
                break
    
    pbar.close()
    logger.info(f"\n✅ DONE! {completed}/{len(products)} products got images.")

asyncio.run(download())
