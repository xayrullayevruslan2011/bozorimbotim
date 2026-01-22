"""
Ma'lumotlar bazasi - SQLite bilan ishlash
Barcha jadvallar va CRUD operatsiyalari shu yerda
"""
import aiosqlite
from typing import Optional, List, Tuple
from datetime import datetime

DATABASE_NAME = "market_bot.db"


async def init_db():
    """Ma'lumotlar bazasini yaratish va jadvallarni boshlash"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Kategoriyalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                emoji TEXT DEFAULT '📦'
            )
        """)
        
        # Mahsulotlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                photo_id TEXT,
                stock INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Savat jadvali
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
        
        # Buyurtmalar jadvali
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
        
        # Buyurtma tafsilotlari
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
        
        await db.commit()
        
        # Boshlang'ich kategoriyalarni qo'shish
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

async def add_user(user_id: int, username: str, full_name: str):
    """Yangi foydalanuvchi qo'shish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
        """, (user_id, username, full_name))
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
    """Barcha foydalanuvchilar ID larini olish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_users_count() -> int:
    """Foydalanuvchilar sonini olish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]


# ============ KATEGORIYA FUNKSIYALARI ============

async def get_categories() -> List[dict]:
    """Barcha kategoriyalarni olish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM categories") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def add_category(name: str, emoji: str = "📦") -> int:
    """Yangi kategoriya qo'shish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO categories (name, emoji) VALUES (?, ?)",
            (name, emoji)
        )
        await db.commit()
        return cursor.lastrowid


async def delete_category(category_id: int):
    """Kategoriyani o'chirish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        await db.commit()


# ============ MAHSULOT FUNKSIYALARI ============

async def add_product(
    category_id: int,
    name: str,
    description: str,
    price: int,
    photo_id: str,
    stock: int = 0
) -> int:
    """Yangi mahsulot qo'shish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO products (category_id, name, description, price, photo_id, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category_id, name, description, price, photo_id, stock))
        await db.commit()
        return cursor.lastrowid


async def get_products_by_category(category_id: int) -> List[dict]:
    """Kategoriya bo'yicha mahsulotlarni olish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM products 
            WHERE category_id = ? AND is_active = 1
        """, (category_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_product(product_id: int) -> Optional[dict]:
    """Bitta mahsulotni olish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_products() -> List[dict]:
    """Barcha mahsulotlarni olish"""
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
    """Mahsulotni o'chirish (soft delete)"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "UPDATE products SET is_active = 0 WHERE id = ?", 
            (product_id,)
        )
        await db.commit()


async def update_product_stock(product_id: int, stock: int):
    """Mahsulot sonini yangilash"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (stock, product_id)
        )
        await db.commit()


# ============ SAVAT FUNKSIYALARI ============

async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    """Savatga mahsulot qo'shish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # Mahsulot savatda bor-yo'qligini tekshirish
        async with db.execute("""
            SELECT id, quantity FROM cart 
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id)) as cursor:
            existing = await cursor.fetchone()
        
        if existing:
            # Mavjud bo'lsa miqdorni oshirish
            new_quantity = existing[1] + quantity
            await db.execute(
                "UPDATE cart SET quantity = ? WHERE id = ?",
                (new_quantity, existing[0])
            )
        else:
            # Yangi qo'shish
            await db.execute("""
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            """, (user_id, product_id, quantity))
        
        await db.commit()


async def get_cart(user_id: int) -> List[dict]:
    """Foydalanuvchi savatini olish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT c.id, c.quantity, p.id as product_id, p.name, p.price, p.photo_id
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_cart_total(user_id: int) -> int:
    """Savat umumiy summasini olish"""
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
    """Savat miqdorini yangilash"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        if quantity <= 0:
            await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        else:
            await db.execute(
                "UPDATE cart SET quantity = ? WHERE id = ?",
                (quantity, cart_id)
            )
        await db.commit()


async def remove_from_cart(cart_id: int):
    """Savatdan mahsulot o'chirish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        await db.commit()


async def clear_cart(user_id: int):
    """Savatni tozalash"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()


# ============ BUYURTMA FUNKSIYALARI ============

async def create_order(user_id: int, phone: str, address: str) -> int:
    """Yangi buyurtma yaratish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # Savat ma'lumotlarini olish
        cart_items = await get_cart(user_id)
        total = await get_cart_total(user_id)
        
        if not cart_items:
            return 0
        
        # Buyurtma yaratish
        cursor = await db.execute("""
            INSERT INTO orders (user_id, total_amount, phone, address)
            VALUES (?, ?, ?, ?)
        """, (user_id, total, phone, address))
        order_id = cursor.lastrowid
        
        # Buyurtma tafsilotlarini qo'shish
        for item in cart_items:
            await db.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item['product_id'], item['quantity'], item['price']))
        
        # Savatni tozalash
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        
        await db.commit()
        return order_id


async def get_order(order_id: int) -> Optional[dict]:
    """Buyurtma ma'lumotlarini olish"""
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


async def get_order_items(order_id: int) -> List[dict]:
    """Buyurtma mahsulotlarini olish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT oi.*, p.name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_orders_count() -> int:
    """Buyurtmalar sonini olish"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM orders") as cursor:
            row = await cursor.fetchone()
            return row[0]
