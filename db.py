import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    # Buyurtmalar jadvalini yaratish
    def create_orders_table(self):
        with self.connection:
            return self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    full_name TEXT,
                    photo_id TEXT,
                    products TEXT,
                    total_price TEXT,
                    track_code TEXT DEFAULT 'Kutilmoqda...',
                    status TEXT DEFAULT 'tekshirilmoqda'
                )
            """)

    # Yangi buyurtma qo'shish
    def add_order(self, user_id, full_name, photo_id, products, total_price):
        with self.connection:
            return self.cursor.execute("""
                INSERT INTO orders (user_id, full_name, photo_id, products, total_price) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, full_name, photo_id, products, total_price)).lastrowid

    # Trek kodni yangilash (Admin uchun)
    def update_track_code(self, order_id, track_code):
        with self.connection:
            return self.cursor.execute("""
                UPDATE orders SET track_code = ?, status = '✅ Yuborildi' 
                WHERE id = ?
            """, (track_code, order_id))

    # Buyurtmani bekor qilish (Admin uchun)
    def reject_order(self, order_id):
        with self.connection:
            return self.cursor.execute("""
                UPDATE orders SET status = '❌ Bekor qilindi' 
                WHERE id = ?
            """, (order_id,))

    # Foydalanuvchi buyurtmalarini olish
    def get_user_orders(self, user_id):
        with self.connection:
            return self.cursor.execute("""
                SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC
            """, (user_id,)).fetchall()
            
    # Bitta buyurtmani olish
    def get_order(self, order_id):
        with self.connection:
            return self.cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

# Bazani ulash
db = Database('database.db')
db.create_orders_table()