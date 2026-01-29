import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_table_orders()

    def create_table_orders(self):
        """Buyurtmalar jadvalini yaratish"""
        with self.connection:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    full_name TEXT,
                    photo_id TEXT,
                    product_name TEXT,
                    price TEXT,
                    track_code TEXT DEFAULT 'Kutilmoqda...',
                    status TEXT DEFAULT 'Tekshirilmoqda...'
                )
            """)

    def add_order(self, user_id, full_name, photo_id, product_name, price):
        """Yangi buyurtma qo'shish"""
        with self.connection:
            self.cursor.execute("INSERT INTO orders (user_id, full_name, photo_id, product_name, price) VALUES (?, ?, ?, ?, ?)",
                                (user_id, full_name, photo_id, product_name, price))
            return self.cursor.lastrowid

    def get_user_orders(self, user_id):
        """Foydalanuvchi buyurtmalarini olish"""
        with self.connection:
            return self.cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()

    def update_order_status(self, order_id, status, track_code=None):
        """Admin uchun: Statusni o'zgartirish"""
        with self.connection:
            if track_code:
                self.cursor.execute("UPDATE orders SET status = ?, track_code = ? WHERE id = ?", (status, track_code, order_id))
            else:
                self.cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

# Obyekt yaratamiz (user.py shu nom bilan chaqiradi)
db = Database('market.db')