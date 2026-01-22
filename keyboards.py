"""
Klaviaturalar - Barcha tugmalar shu yerda
Reply va Inline tugmalar
"""
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List
from config import ADMIN_USERNAME


# ============ ASOSIY MENYU ============

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy menyu tugmalari"""
    builder = ReplyKeyboardBuilder()
    
    # Asosiy tugmalar
    builder.row(
        KeyboardButton(text="🛍 Mahsulotlar"),
        KeyboardButton(text="🛒 Savat")
    )
    builder.row(
        KeyboardButton(text="📦 Mening buyurtmalarim"),
        KeyboardButton(text="📞 Biz bilan aloqa")
    )
    builder.row(
        KeyboardButton(text="ℹ️ Ma'lumot"),
        KeyboardButton(text="⚙️ Sozlamalar")
    )
    
    # Admin uchun qo'shimcha tugma
    if is_admin:
        builder.row(KeyboardButton(text="👨‍💼 Admin Panel"))
    
    return builder.as_markup(resize_keyboard=True)


def get_back_button() -> ReplyKeyboardMarkup:
    """Orqaga tugmasi"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🔙 Orqaga"))
    return builder.as_markup(resize_keyboard=True)


def get_cancel_button() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


def get_skip_button() -> ReplyKeyboardMarkup:
    """O'tkazib yuborish tugmasi"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭ O'tkazib yuborish"),
        KeyboardButton(text="❌ Bekor qilish")
    )
    return builder.as_markup(resize_keyboard=True)


# ============ KATEGORIYALAR ============

def get_categories_keyboard(categories: List[dict]) -> InlineKeyboardMarkup:
    """Kategoriyalar inline tugmalari"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"{category['emoji']} {category['name']}",
                callback_data=f"category_{category['id']}"
            )
        )
    
    return builder.as_markup()


def get_admin_categories_keyboard(categories: List[dict]) -> InlineKeyboardMarkup:
    """Admin uchun kategoriyalar (o'chirish tugmasi bilan)"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"{category['emoji']} {category['name']}",
                callback_data=f"admin_cat_{category['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"delete_cat_{category['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Yangi kategoriya",
            callback_data="add_category"
        )
    )
    
    return builder.as_markup()


# ============ MAHSULOTLAR ============

def get_product_keyboard(product_id: int, in_cart: bool = False) -> InlineKeyboardMarkup:
    """Mahsulot tugmalari"""
    builder = InlineKeyboardBuilder()
    
    if in_cart:
        builder.row(
            InlineKeyboardButton(
                text="✅ Savatda",
                callback_data=f"in_cart_{product_id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="🛒 Savatga qo'shish",
                callback_data=f"add_cart_{product_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Orqaga",
            callback_data="back_to_categories"
        )
    )
    
    return builder.as_markup()


def get_products_navigation(
    category_id: int, 
    current_index: int, 
    total: int,
    product_id: int
) -> InlineKeyboardMarkup:
    """Mahsulotlar bo'ylab navigatsiya"""
    builder = InlineKeyboardBuilder()
    
    # Savatga qo'shish tugmasi
    builder.row(
        InlineKeyboardButton(
            text="🛒 Savatga qo'shish",
            callback_data=f"add_cart_{product_id}"
        )
    )
    
    # Navigatsiya tugmalari
    nav_buttons = []
    
    if current_index > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"prod_nav_{category_id}_{current_index - 1}"
            )
        )
    
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{current_index + 1}/{total}",
            callback_data="current_page"
        )
    )
    
    if current_index < total - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"prod_nav_{category_id}_{current_index + 1}"
            )
        )
    
    builder.row(*nav_buttons)
    
    # Orqaga tugmasi
    builder.row(
        InlineKeyboardButton(
            text="🔙 Kategoriyalarga",
            callback_data="back_to_categories"
        )
    )
    
    return builder.as_markup()


def get_admin_products_keyboard(products: List[dict]) -> InlineKeyboardMarkup:
    """Admin uchun mahsulotlar ro'yxati"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {product['name']} - {product['price']:,} so'm",
                callback_data=f"admin_prod_{product['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"delete_prod_{product['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Yangi mahsulot",
            callback_data="add_product"
        )
    )
    
    return builder.as_markup()


# ============ SAVAT ============

def get_cart_keyboard(cart_items: List[dict]) -> InlineKeyboardMarkup:
    """Savat tugmalari"""
    builder = InlineKeyboardBuilder()
    
    for item in cart_items:
        builder.row(
            InlineKeyboardButton(
                text="➖",
                callback_data=f"cart_minus_{item['id']}"
            ),
            InlineKeyboardButton(
                text=f"{item['name']} ({item['quantity']}x)",
                callback_data=f"cart_item_{item['id']}"
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=f"cart_plus_{item['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"cart_remove_{item['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Buyurtmani rasmiylashtirish",
            callback_data="checkout"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🗑 Savatni tozalash",
            callback_data="clear_cart"
        )
    )
    
    return builder.as_markup()


def get_empty_cart_keyboard() -> InlineKeyboardMarkup:
    """Bo'sh savat tugmalari"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛍 Xarid qilish",
            callback_data="go_shopping"
        )
    )
    return builder.as_markup()


# ============ BUYURTMA ============

def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqam tugmasi"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)
    )
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


def get_confirm_order_keyboard() -> InlineKeyboardMarkup:
    """Buyurtmani tasdiqlash"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")
    )
    return builder.as_markup()


# ============ ALOQA ============

def get_contact_keyboard() -> InlineKeyboardMarkup:
    """Aloqa tugmalari"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="💬 Admin bilan bog'lanish",
            url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✍️ Xabar qoldirish",
            callback_data="leave_feedback"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📍 Manzilimiz",
            callback_data="show_location"
        )
    )
    
    return builder.as_markup()


# ============ ADMIN PANEL ============

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Admin panel tugmalari"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin_products"),
        InlineKeyboardButton(text="📁 Kategoriyalar", callback_data="admin_categories")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
        InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Buyurtmalar", callback_data="admin_orders")
    )
    
    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Xabar yuborishni tasdiqlash"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Yuborish", callback_data="confirm_broadcast"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
    )
    return builder.as_markup()


def get_admin_select_category_keyboard(categories: List[dict]) -> InlineKeyboardMarkup:
    """Mahsulot qo'shish uchun kategoriya tanlash"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"{category['emoji']} {category['name']}",
                callback_data=f"select_cat_{category['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="cancel_add_product"
        )
    )
    
    return builder.as_markup()
