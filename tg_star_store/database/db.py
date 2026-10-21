import aiosqlite
from pathlib import Path

DB_PATH = Path("data/bot.db")

async def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance_stars REAL DEFAULT 0,
                balance_ton REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount_stars REAL,
                amount_ton REAL,
                status TEXT,
                tx_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_or_create_user(user_id: int, username: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row
        await db.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def create_order(user_id: int, order_type: str, amount_stars: float, amount_ton: float):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO orders (user_id, type, amount_stars, amount_ton, status) VALUES (?, ?, ?, ?, 'pending')",
            (user_id, order_type, amount_stars, amount_ton)
        )
        await db.commit()
        return cursor.lastrowid

async def update_order_status(order_id: int, status: str, tx_hash: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if tx_hash:
            await db.execute(
                "UPDATE orders SET status = ?, tx_hash = ? WHERE id = ?",
                (status, tx_hash, order_id)
            )
        else:
            await db.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id)
            )
        await db.commit()

async def get_pending_orders(user_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if user_id:
            async with db.execute(
                "SELECT * FROM orders WHERE user_id = ? AND status = 'pending'",
                (user_id,)
            ) as cursor:
                return await cursor.fetchall()
        async with db.execute("SELECT * FROM orders WHERE status = 'pending'") as cursor:
            return await cursor.fetchall()
