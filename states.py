"""
FSM States - Bot holatlari
Mahsulot qo'shish, buyurtma berish va boshqa jarayonlar uchun
"""
from aiogram.fsm.state import State, StatesGroup


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


class OrderState(StatesGroup):
    """Buyurtma berish holatlari"""
    phone = State()         # Telefon raqam
    address = State()       # Manzil
    confirm = State()       # Tasdiqlash


class BroadcastState(StatesGroup):
    """Xabar yuborish holatlari"""
    message = State()       # Xabar matni
    confirm = State()       # Tasdiqlash


class ContactState(StatesGroup):
    """Aloqa holatlari"""
    message = State()       # Xabar
