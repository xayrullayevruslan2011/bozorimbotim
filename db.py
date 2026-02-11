import aiosqlite
from database import DATABASE_NAME
from aiogram import Bot

class Database:
    def __init__(self):
        self.db_name = DATABASE_NAME

    async def add_order(self, user_id, full_name, photo_id, product_name, status):
        """
        user.py dan keladigan chek va buyurtmani saqlash.
        Bu yerda biz alohida 'order_checks' jadvalini ishlatamiz.
        """
        async with aiosqlite.connect(self.db_name) as db:
            # 1. Jadval borligini tekshiramiz (agar yo'q bo'lsa yaratamiz)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS order_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    full_name TEXT,
                    photo_id TEXT,
                    product_name TEXT,
                    status TEXT,
                    track_code TEXT DEFAULT 'Kutilmoqda...',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. Ma'lumotni qo'shamiz
            cursor = await db.execute("""
                INSERT INTO order_checks (user_id, full_name, photo_id, product_name, status)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, full_name, photo_id, product_name, status))
            
            await db.commit()
            return cursor.lastrowid

    async def get_user_orders(self, user_id):
        """
        Foydalanuvchining barcha buyurtmalarini olish.
        user.py kutayotgan formatda qaytaradi.
        """
        async with aiosqlite.connect(self.db_name) as db:
            # Xatolik bo'lmasligi uchun jadval borligini yana tekshiramiz
            await db.execute("""
                CREATE TABLE IF NOT EXISTS order_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    full_name TEXT,
                    photo_id TEXT,
                    product_name TEXT,
                    status TEXT,
                    track_code TEXT DEFAULT 'Kutilmoqda...',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            async with db.execute("SELECT * FROM order_checks WHERE user_id = ? ORDER BY id DESC", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                
                results = []
                for row in rows:
                    # Bazadan kelgan ma'lumot: 
                    # (0:id, 1:user_id, 2:full_name, 3:photo_id, 4:product_name, 5:status, 6:track_code, 7:created_at)
                    
                    # user.py da biz shunday o'qiyapmiz:
                    # order[0] -> id
                    # order[3] -> photo_id (rasm)
                    # order[4] -> product_name (mahsulot nomi)
                    # order[6] -> track_code
                    # order[7] -> status
                    
                    # Shuning uchun tartibini moslab qaytaramiiz:
                    results.append((
                        row[0], # id
                        row[1], # user_id
                        row[2], # full_name
                        row[3], # photo_id
                        row[4], # product_name
                        0,      # Narx (hozircha shart emas)
                        row[6], # Track code
                        row[5]  # status
                    ))
                return results

# Bot ishlatishi uchun obyekt yaratamiz
db = Database()
# Bu kodni user ulanish (start) jarayoniga qo'shish kerak
async def notify_inviter(bot: Bot, inviter_id: int, new_user_name: str):
    try:
        await bot.send_message(
            inviter_id, 
            f"🎁 **Yangi referal!**\n\nDo'stingiz {new_user_name} ulandi. Balansingizga 500 so'm qo'shildi! ✅"
        )
    except Exception:
        pass # Agar inviter botni bloklagan bo'lsa xato bermasligi uchun
    # db.py ichiga
async def get_all_products():
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT name, price, media_ids FROM products") as cursor:
            return await cursor.fetchall()
        # db.py ichida
async def create_tables():
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price INTEGER,
                media_ids TEXT  -- Mana shu yerga hamma file_id'lar yoziladi
            )
        """)
        await db.commit()
        # db.py ichiga
async def add_product(name, price, media_ids):
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute(
            "INSERT INTO products (name, price, media_ids) VALUES (?, ?, ?)",
            (name, price, media_ids)
        )
        await db.commit()