import aiosqlite
from database import DATABASE_NAME

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