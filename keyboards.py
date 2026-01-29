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
from aiogram.types.web_app_info import WebAppInfo 
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List
from config import ADMIN_USERNAME

# SIZNING YANGI VERCEL SAYTINGIZ
NASIYA_URL = "https://nasiyaruslan.vercel.app"


# ============ ASOSIY MENYU (O'ZGARTIRILDI) ✅ ============

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy menyu tugmalari"""
    builder = ReplyKeyboardBuilder()
    
    # 1-qator: Mahsulotlar va Kurslar
    builder.row(
        KeyboardButton(text="🛍 Mahsulotlar"),
        KeyboardButton(text="🎓 Online Kurslar")
    )
    
    # 2-qator: Savat va Buyurtmalar ("Limit olish" olib tashlandi, o'rni to'ldirildi)
    builder.row(
        KeyboardButton(text="🛒 Savat"),
        KeyboardButton(text="📦 Mening buyurtmalarim")
    )
    
    # 3-qator: Aloqa va Sozlamalar
    builder.row(
        KeyboardButton(text="📞 Biz bilan aloqa"),
        KeyboardButton(text="⚙️ Sozlamalar")
    )
    
    # 4-qator: Ma'lumot va YANGI BO'LIM (Siz so'ragan joy)
    builder.row(
        KeyboardButton(text="ℹ️ Ma'lumot"),
        KeyboardButton(text="📂 Yangi Bo'lim") # <-- Nomini o'zingizga moslab o'zgartiring
    )
    
    # Admin uchun
    if is_admin:
        builder.row(KeyboardButton(text="👨‍💼 Admin Panel"))
    
    return builder.as_markup(resize_keyboard=True)


# ============ SAYTGA O'TISH TUGMASI (KURSLAR) ============
def get_website_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="↗️ Platformaga kirish", 
            url="https://online-kurs-kmkn.vercel.app/" 
        )
    )
    return builder.as_markup()

# ============ LIMIT OLISH TUGMASI (INLINE) ============
# Bu tugma menyuda ko'rinmaydi, lekin kod ichida kerak bo'lsa turgani ma'qul
def get_limit_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🚀 Limitni tekshirish", 
            web_app=WebAppInfo(url=NASIYA_URL) 
        )
    )
    return builder.as_markup()


# ============ NASIYA VA KIYIMLAR UCHUN TUGMALAR ============

def get_buy_button(product_name: str, price: int) -> InlineKeyboardMarkup:
    """
    UNIVERSAL NASIYA TUGMASI
    """
    full_url = f"{NASIYA_URL}?name={product_name}&price={price}"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💳 Nasiyaga olish", 
            web_app=WebAppInfo(url=full_url)
        )
    )
    return builder.as_markup()

def get_clothing_keyboard() -> InlineKeyboardMarkup:
    """
    Jinsi va Bryuk uchun maxsus tugmalar
    """
    builder = InlineKeyboardBuilder()
    
    # 1. Oversize Jeans (170 000)
    url_jeans = f"{NASIYA_URL}?name=Oversize Jeans&price=170000"
    builder.row(
        InlineKeyboardButton(
            text="👖 Oversize Jeans - Nasiya", 
            web_app=WebAppInfo(url=url_jeans)
        )
    )
    
    # 2. Oversize Bryuk (90 000)
    url_bryuk = f"{NASIYA_URL}?name=Oversize Bryuk&price=90000"
    builder.row(
        InlineKeyboardButton(
            text="👖 Oversize Bryuk - Nasiya", 
            web_app=WebAppInfo(url=url_bryuk)
        )
    )
    
    return builder.as_markup()


# ============ QOLGAN ESKI TUGMALAR (O'ZGARISHSIZ) ============

def get_back_button() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🔙 Orqaga"))
    return builder.as_markup(resize_keyboard=True)

def get_cancel_button() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)

def get_skip_button() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭ O'tkazib yuborish"),
        KeyboardButton(text="❌ Bekor qilish")
    )
    return builder.as_markup(resize_keyboard=True)

def get_categories_keyboard(categories: List[dict]) -> InlineKeyboardMarkup:
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
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(
            InlineKeyboardButton(text=f"{category['emoji']} {category['name']}", callback_data=f"admin_cat_{category['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_cat_{category['id']}")
        )
    builder.row(InlineKeyboardButton(text="➕ Yangi kategoriya", callback_data="add_category"))
    return builder.as_markup()

def get_product_keyboard(product_id: int, in_cart: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if in_cart:
        builder.row(InlineKeyboardButton(text="✅ Savatda", callback_data=f"in_cart_{product_id}"))
    else:
        builder.row(InlineKeyboardButton(text="🛒 Savatga qo'shish", callback_data=f"add_cart_{product_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_categories"))
    return builder.as_markup()

def get_products_navigation(category_id: int, current_index: int, total: int, product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛒 Savatga qo'shish", callback_data=f"add_cart_{product_id}"))
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"prod_nav_{category_id}_{current_index - 1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="current_page"))
    if current_index < total - 1:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"prod_nav_{category_id}_{current_index + 1}"))
    builder.row(*nav_buttons)
    builder.row(InlineKeyboardButton(text="🔙 Kategoriyalarga", callback_data="back_to_categories"))
    return builder.as_markup()

def get_admin_products_keyboard(products: List[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(
            InlineKeyboardButton(text=f"📦 {product['name']} - {product['price']:,} so'm", callback_data=f"admin_prod_{product['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_prod_{product['id']}")
        )
    builder.row(InlineKeyboardButton(text="➕ Yangi mahsulot", callback_data="add_product"))
    return builder.as_markup()

def get_cart_keyboard(cart_items: List[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        builder.row(
            InlineKeyboardButton(text="➖", callback_data=f"cart_minus_{item['id']}"),
            InlineKeyboardButton(text=f"{item['name']} ({item['quantity']}x)", callback_data=f"cart_item_{item['id']}"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_plus_{item['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"cart_remove_{item['id']}")
        )
    builder.row(InlineKeyboardButton(text="✅ Buyurtmani rasmiylashtirish", callback_data="checkout"))
    builder.row(InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart"))
    return builder.as_markup()

def get_empty_cart_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛍 Xarid qilish", callback_data="go_shopping"))
    return builder.as_markup()

def get_phone_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True))
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)

def get_confirm_order_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order"), InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order"))
    return builder.as_markup()

def get_contact_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💬 Admin bilan bog'lanish", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"))
    builder.row(InlineKeyboardButton(text="✍️ Xabar qoldirish", callback_data="leave_feedback"))
    builder.row(InlineKeyboardButton(text="📍 Manzilimiz", callback_data="show_location"))
    return builder.as_markup()

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin_products"), InlineKeyboardButton(text="📁 Kategoriyalar", callback_data="admin_categories"))
    builder.row(InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"), InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text="📋 Buyurtmalar", callback_data="admin_orders"))
    return builder.as_markup()

def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Yuborish", callback_data="confirm_broadcast"), InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast"))
    return builder.as_markup()

def get_admin_select_category_keyboard(categories: List[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(InlineKeyboardButton(text=f"{category['emoji']} {category['name']}", callback_data=f"select_cat_{category['id']}"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_add_product"))
    return builder.as_markup()

# ============ MAJBURIY OBUNA ============

def get_subscription_keyboard():
    """Majburiy obuna uchun tugmalar"""
    builder = InlineKeyboardBuilder()
    
    # 1. Kanallarga linklar
    builder.row(InlineKeyboardButton(text="📢 1-Kanalga a'zo bo'lish", url="https://t.me/xitoybozor_n1"))
    builder.row(InlineKeyboardButton(text="📢 2-Kanalga a'zo bo'lish", url="https://t.me/xitoydarslik_navoiy"))
    
    # 2. Tekshirish tugmasi
    builder.row(InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription"))
    
    return builder.as_markup()
# =========================================================
# 🆕 YANGI QO'SHILGAN KODLAR (TO'LOV VA BUYURTMALAR UCHUN)
# =========================================================

def get_payment_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Foydalanuvchi chek yuborish jarayonida bekor qilishi uchun
    """
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ To'lovni bekor qilish"))
    return builder.as_markup(resize_keyboard=True)

def get_admin_check_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    Admin foydalanuvchi chekini ko'rganda chiqadigan tugmalar.
    order_id - bu qaysi buyurtmaligini bilish uchun kerak.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Tasdiqlash va Trek berish", 
            callback_data=f"admin_confirm_{order_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Rad etish", 
            callback_data=f"admin_reject_{order_id}"
        )
    )
    return builder.as_markup()

def get_user_orders_navigation(current_index: int, total_orders: int) -> InlineKeyboardMarkup:
    """
    'Mening buyurtmalarim' bo'limida bittadan varaqlash uchun tugmalar.
    """
    builder = InlineKeyboardBuilder()
    buttons = []

    # Agar birinchi buyurtma bo'lmasa, "Oldingi" tugmasini qo'shish
    if current_index > 0:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"my_orders_prev_{current_index}"))

    # O'rtada sahifa raqami (masalan: 1/5)
    buttons.append(InlineKeyboardButton(text=f"{current_index + 1} / {total_orders}", callback_data="noop"))

    # Agar oxirgi buyurtma bo'lmasa, "Keyingi" tugmasini qo'shish
    if current_index < total_orders - 1:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"my_orders_next_{current_index}"))

    builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="❌ Yopish", callback_data="close_my_orders"))
    
    return builder.as_markup()
# ... (Yuqoridagi eski kodlaringiz turaversin) ...

# ============ 🎓 YANGI: KURSLAR VA TO'LOV TUGMALARI ============

def get_tariffs_keyboard() -> InlineKeyboardMarkup:
    """
    1-QADAM: Tariflarni tanlash uchun tugmalar
    """
    builder = InlineKeyboardBuilder()
    
    # Tariflar
    builder.row(InlineKeyboardButton(text="🔵 Start Tarifi (50 000 so'm)", callback_data="tariff_start"))
    builder.row(InlineKeyboardButton(text="🟠 Pro Tarifi (70 000 so'm)", callback_data="tariff_pro"))
    builder.row(InlineKeyboardButton(text="🟣 VIP Tarifi (100 000 so'm)", callback_data="tariff_vip"))
    
    # Yopish tugmasi
    builder.row(InlineKeyboardButton(text="❌ Yopish", callback_data="delete_message"))
    
    return builder.as_markup()

def get_payment_actions_keyboard(price_text: str) -> InlineKeyboardMarkup:
    """
    2-QADAM: To'lov qilish menyusi (Nusxalash tugmalari bilan)
    price_text: Masalan '100 000'
    """
    builder = InlineKeyboardBuilder()

    # 1. Tekshirish
    builder.row(InlineKeyboardButton(text="♻️ Tekshirish", callback_data="check_payment"))

    # 2. Karta raqamni nusxalash (Bosilganda raqamni yuboramiz)
    builder.row(InlineKeyboardButton(text="💳 Karta raqamni nusxalash * 5457", callback_data="copy_card_number"))

    # 3. Summani nusxalash
    builder.row(InlineKeyboardButton(text=f"💰 To'lov miqdorini nusxalash - {price_text} so'm", callback_data=f"copy_amount_{price_text}"))

    # 4. Bekor qilish
    builder.row(InlineKeyboardButton(text="❌ To'lovni bekor qilish", callback_data="delete_message"))

    return builder.as_markup()