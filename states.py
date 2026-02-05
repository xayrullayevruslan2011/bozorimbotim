"""
FSM States - Bot holatlari
Mahsulot qo'shish, buyurtma berish va boshqa jarayonlar uchun
"""
from aiogram.fsm.state import State, StatesGroup

class ContactState(StatesGroup):
    """Aloqa holatlari"""
    message = State()

class CheckoutState(StatesGroup):
    """Online Kurslar uchun to'lov qilish holati"""
    waiting_for_receipt = State()

class OrderState(StatesGroup):
    """Savatdan Buyurtma berish holatlari"""
    phone = State()             # Telefon raqam
    address = State()           # Manzil
    confirm = State()           # Tasdiqlash
    waiting_for_receipt = State() # <--- YANGI: Chek rasmini kutish

class AddProductState(StatesGroup):
    """Mahsulot qo'shish holatlari"""
    category = State()      # Kategoriyani tanlash
    name = State()          # Mahsulot nomi
    description = State()   # Tavsif
    price = State()         # Narx
    photo = State()         # Rasm
    stock = State()         # Ombordagi soni

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

class AddProduct(StatesGroup):
    """Qo'shimcha mahsulot holatlari (Zaxira)"""
    name = State()
    price = State()
    media = State()