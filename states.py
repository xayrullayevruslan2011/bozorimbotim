"""
FSM States - Bot holatlari
Mahsulot qo'shish, buyurtma berish va boshqa jarayonlar uchun
"""
from aiogram.fsm.state import State, StatesGroup

class ContactState(StatesGroup):
    """Aloqa holatlari"""
    message = State()

class CheckoutState(StatesGroup):
    """Online Kurslar va To'lov uchun"""
    waiting_for_receipt = State()

class OrderState(StatesGroup):
    """Savatdan Buyurtma berish holatlari"""
    phone = State()             # Telefon raqam
    address = State()           # Manzil
    confirm = State()           # Tasdiqlash
    waiting_for_receipt = State() # Chek rasmini kutish

class AddProductState(StatesGroup):
    """Mahsulot qo'shish holatlari (Admin)"""
    category = State()      # 1. Kategoriyani tanlash
    name = State()          # 2. Mahsulot nomi
    price = State()         # 3. Narx
    size = State()          # 4. Razmer (Yangi qo'shildi) ✅
    description = State()   # 5. Tavsif
    photo = State()         # 6. Rasm/Video
    stock = State()         # 7. Ombordagi soni (Yangi qo'shildi) ✅

class AddCategoryState(StatesGroup):
    """Kategoriya qo'shish holatlari"""
    name = State()          # Kategoriya nomi
    emoji = State()         # Emoji

class BroadcastState(StatesGroup):
    """Xabar yuborish holatlari"""
    message = State()       # Xabar matni
    confirm = State()       # Tasdiqlash

class AdminState(StatesGroup):
    """Admin buyurtmani tasdiqlash holati"""
    waiting_for_track = State() # Admin trek kod yozishi kerak