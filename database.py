"""
Ma'lumotlar bazasi - SQLite bilan ishlash
Tahrirlangan: Razmer, Custom ID, Statistika, Chek va Aqlli Qidiruv tizimi.
"""
import aiosqlite
import random
from typing import Optional, List, Tuple
from datetime import datetime

DATABASE_NAME = "market_bot.db"


async def init_db():
    """Ma'lumotlar bazasini yaratish va jadvallarni boshlash"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # 1. Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                custom_id INTEGER,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                referrer_id INTEGER,
                balance INTEGER DEFAULT 0,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Kategoriyalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                emoji TEXT DEFAULT '📦'
            )
        """)
        
        # 3. Mahsulotlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                size TEXT,
                photo_id TEXT,
                stock INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # 4. Savat jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # 5. Buyurtmalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_amount INTEGER,
                status TEXT DEFAULT 'pending',
                phone TEXT,
                address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 6. Buyurtma tafsilotlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                price INTEGER,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # 7. Cheklar jadvali (To'lovni tekshirish uchun)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS order_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                photo_id TEXT,
                product_name TEXT,
                status TEXT DEFAULT 'Tekshirilmoqda',
                track_code TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
        await add_default_categories()


async def add_default_categories():
    """Standart kategoriyalarni qo'shish"""
    categories = [
        ("👔 Kiyimlar", "👔"),
        ("📱 Elektronika", "📱"),
        ("🍎 Oziq-ovqat", "🍎"),
        ("🏠 Uy-ro'zg'or", "🏠"),
        ("⚽ Sport", "⚽"),
    ]
    
    async with aiosqlite.connect(DATABASE_NAME) as db:
        for name, emoji in categories:
            try:
                await db.execute(
                    "INSERT OR IGNORE INTO categories (name, emoji) VALUES (?, ?)",
                    (name, emoji)
                )
            except:
                pass
        await db.commit()


# ============ FOYDALANUVCHI FUNKSIYALARI ============

async def add_user(user_id: int, username: str, full_name: str, referrer_id: int = None):
    """Yangi foydalanuvchi qo'shish (Random ID va Referal bilan)"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            existing_user = await cursor.fetchone()

        if existing_user:
            await db.execute("""
                UPDATE users SET username = ?, full_name = ? WHERE user_id = ?
            """, (username, full_name, user_id))
        else:
            custom_id = random.randint(1000, 9999) 
            reg_date = datetime.now().strftime("%Y-%m-%d %H:%M")

            await db.execute("""
                INSERT INTO users (user_id, custom_id, username, full_name, referrer_id, balance, registered_at)
                VALUES (?, ?, ?, ?, ?, 0, ?)
            """, (user_id, custom_id, username, full_name, referrer_id, reg_date))
            
            if referrer_id:
                BONUS_AMOUNT = 50 
                await db.execute("""
                    UPDATE users SET balance = balance + ? WHERE user_id = ?
                """, (BONUS_AMOUNT, referrer_id))

        await db.commit()


async def get_user(user_id: int) -> Optional[dict]:
    """Foydalanuvchi ma'lumotlarini olish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_users() -> List[int]:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_users_count() -> int:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]


async def get_user_balance(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_referrals_count(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0]


# ============ STATISTIKA VA TOP REFERALLAR ============

async def get_top_referrals():
    """Eng ko'p referal chaqirgan TOP 10 talik"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        query = """
            SELECT u.full_name, COUNT(r.user_id) as referral_count
            FROM users u
            LEFT JOIN users r ON u.user_id = r.referrer_id
            WHERE r.user_id IS NOT NULL
            GROUP BY u.user_id
            ORDER BY referral_count DESC
            LIMIT 10
        """
        async with db.execute(query) as cursor:
            return await cursor.fetchall()

async def get_user_stats(user_id):
    """Foydalanuvchining to'liq statistikasi"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT full_name, balance, registered_at, custom_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_data = await cursor.fetchone()
        
        if not user_data: return None
        
        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,)) as cursor:
            ref_count = (await cursor.fetchone())[0]
            
        return (user_data[0], user_data[1], ref_count, user_data[2])


# ============ KATEGORIYA VA MAHSULOTLAR ============

async def get_categories() -> List[dict]:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM categories") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def add_category(name: str, emoji: str = "📦") -> int:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO categories (name, emoji) VALUES (?, ?)",
            (name, emoji)
        )
        await db.commit()
        return cursor.lastrowid

async def delete_category(category_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        await db.commit()

async def add_product(category_id: int, name: str, description: str, price: int, size: str, photo_id: str, stock: int = 0) -> int:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO products (category_id, name, description, price, size, photo_id, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (category_id, name, description, price, size, photo_id, stock))
        await db.commit()
        return cursor.lastrowid

async def get_products_by_category(category_id: int) -> List[dict]:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE category_id = ?", (category_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_product(product_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE id = ?", (product_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_all_products() -> List[dict]:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def delete_product(product_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
        await db.commit()


# ============ SAVAT FUNKSIYALARI ============

async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("""
            SELECT id, quantity FROM cart 
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id)) as cursor:
            existing = await cursor.fetchone()
        
        if existing:
            new_quantity = existing[1] + quantity
            await db.execute("UPDATE cart SET quantity = ? WHERE id = ?", (new_quantity, existing[0]))
        else:
            await db.execute("""
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            """, (user_id, product_id, quantity))
        await db.commit()

async def get_cart(user_id: int) -> List[dict]:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT c.id, c.quantity, p.id as product_id, p.name, p.price, p.photo_id, p.size
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_cart_total(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("""
            SELECT SUM(c.quantity * p.price) as total
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] or 0

async def update_cart_quantity(cart_id: int, quantity: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        if quantity <= 0:
            await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        else:
            await db.execute("UPDATE cart SET quantity = ? WHERE id = ?", (quantity, cart_id))
        await db.commit()

async def remove_from_cart(cart_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        await db.commit()

async def clear_cart(user_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()


# ============ BUYURTMA VA CHEK FUNKSIYALARI ============

async def create_order(user_id: int, phone: str, address: str) -> int:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cart_items = await get_cart(user_id)
        total = await get_cart_total(user_id)
        
        if not cart_items:
            return 0
        
        cursor = await db.execute("""
            INSERT INTO orders (user_id, total_amount, phone, address)
            VALUES (?, ?, ?, ?)
        """, (user_id, total, phone, address))
        order_id = cursor.lastrowid
        
        for item in cart_items:
            await db.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item['product_id'], item['quantity'], item['price']))
        
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()
        return order_id

async def get_order(order_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT o.*, u.username, u.full_name
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.id = ?
        """, (order_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_orders_count() -> int:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM orders") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()

async def add_order(user_id: int, full_name: str, photo_id: str, product_name: str, status: str) -> int:
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO order_checks (user_id, full_name, photo_id, product_name, status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, full_name, photo_id, product_name, status))
        await db.commit()
        return cursor.lastrowid

async def get_user_orders(user_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT * FROM order_checks WHERE user_id = ? ORDER BY id DESC", (user_id,)) as cursor:
            return await cursor.fetchall()


# ============ 🔥 YANGI: AQLLI QIDIRUV FUNKSIYASI 🔥 ============

async def search_products(query: str) -> List[dict]:
    """Mahsulotlarni nomi bo'yicha qidirish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        # %query% patterni nomi ichida shu so'z bor hamma mahsulotni topadi
        async with db.execute(
            "SELECT * FROM products WHERE name LIKE ? ORDER BY id DESC", 
            (f"%{query}%",)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]