"""
Klaviaturalar - TO'LIQ VA KENGAYTIRILGAN VERSIYA
Barcha funksiyalar jamlangan:
1. Asosiy menyu (Qidiruv bilan)
2. Kabinet va Referallar
3. Online Kurslar va To'lov
4. Admin Panel (To'liq)
5. Do'kon (Kategoriya, Mahsulot, Savat)
6. Buyurtmalar tarixi
7. Qo'shimcha (Nasiya, Kiyimlar, Aloqa)
8. Yordamchi tugmalar
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

# LINKLAR
NASIYA_URL = "https://nasiyaruslan.vercel.app"
PLATFORM_URL = "https://online-kurs-kmkn.vercel.app/"


# =========================================================
# 1. ASOSIY MENYU TUGMALARI
# =========================================================

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy menyu (User va Admin uchun)"""
    builder = ReplyKeyboardBuilder()
    
    # 1-qator: Savdo va Qidiruv
    builder.row(
        KeyboardButton(text="🛍 Mahsulotlar"),
        KeyboardButton(text="🔍 Qidiruv") # YANGI QO'SHILDI ✅
    )
    
    # 2-qator: Kurslar va Savat
    builder.row(
        KeyboardButton(text="🎓 Online Kurslar"),
        KeyboardButton(text="🛒 Savat")
    )
    
    # 3-qator: Buyurtmalar va Ruslan | Shop
    builder.row(
        KeyboardButton(text="📦 Mening buyurtmalarim"),
        KeyboardButton(text="🛍 Ruslan | Shop") # <--- MANA SHU YER O'ZGARDI ✅
    )
    
    # 4-qator: Kabinet va Sozlama
    builder.row(
        KeyboardButton(text="📂 Yangi Bo'lim"), 
        KeyboardButton(text="⚙️ Sozlamalar")
    )

    # 5-qator: Aloqa va Ma'lumot
    builder.row(
        KeyboardButton(text="📞 Biz bilan aloqa"),
        KeyboardButton(text="ℹ️ Ma'lumot")
    )

    # Admin bo'lsa
    if is_admin:
        builder.row(KeyboardButton(text="👨‍💼 Admin Panel"))
    
    return builder.as_markup(resize_keyboard=True)


# =========================================================
# 2. YANGI BO'LIM (KABINET) TUGMALARI
# =========================================================

def get_cabinet_keyboard() -> InlineKeyboardMarkup:
    """Kabinet ichidagi barcha tugmalar"""
    builder = InlineKeyboardBuilder()
    
    # 1. Pul ishlash
    builder.row(InlineKeyboardButton(text="💰 Pul ishlash (Referal)", callback_data="earn_money"))
    
    # 2. Statistika va Reyting
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="my_stats"),
        InlineKeyboardButton(text="🏆 TOP 10 Reyting", callback_data="top_10")
    )
    
    # 3. Pul yechish
    builder.row(InlineKeyboardButton(text="📤 Pulni yechib olish", callback_data="withdraw_money"))
    
    # 4. Yopish
    builder.row(InlineKeyboardButton(text="❌ Yopish", callback_data="delete_message"))
    
    return builder.as_markup()


# =========================================================
# 3. ONLINE KURSLAR VA TO'LOV TIZIMI
# =========================================================

def get_tariffs_keyboard() -> InlineKeyboardMarkup:
    """Kurs tariflarini tanlash"""
    builder = InlineKeyboardBuilder()
    
    # Tariflar
    builder.row(InlineKeyboardButton(text="🔵 Start Tarifi (50 000 so'm)", callback_data="tariff_start"))
    builder.row(InlineKeyboardButton(text="🟠 Pro Tarifi (70 000 so'm)", callback_data="tariff_pro"))
    builder.row(InlineKeyboardButton(text="🟣 VIP Tarifi (100 000 so'm)", callback_data="tariff_vip"))
    
    # Yopish
    builder.row(InlineKeyboardButton(text="❌ Yopish", callback_data="delete_message"))
    return builder.as_markup()

def get_payment_actions_keyboard(price_text: str) -> InlineKeyboardMarkup:
    """To'lov qilish menyusi"""
    builder = InlineKeyboardBuilder()
    
    # 1. Tekshirish
    builder.row(InlineKeyboardButton(text="♻️ To'lovni tekshirish", callback_data="check_payment"))
    
    # 2. Karta nusxalash
    builder.row(InlineKeyboardButton(text="💳 Karta raqamni nusxalash", callback_data="copy_card_number"))
    
    # 3. Summa nusxalash
    builder.row(InlineKeyboardButton(text=f"💰 Summani nusxalash ({price_text})", callback_data=f"copy_amount_{price_text}"))
    
    # 4. Bekor qilish
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="delete_message"))
    return builder.as_markup()

def get_payment_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Rasm yuborishni bekor qilish (Reply)"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ To'lovni bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


# =========================================================
# 4. ADMIN PANEL VA BOSHQARUV
# =========================================================

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Admin asosiy menyusi"""
    b = InlineKeyboardBuilder()
    # Mahsulot va Kategoriya
    b.row(
        InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin_products"), 
        InlineKeyboardButton(text="📁 Kategoriyalar", callback_data="admin_categories")
    )
    # Stats va Broadcast
    b.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"), 
        InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")
    )
    # Buyurtmalar
    b.row(InlineKeyboardButton(text="📋 Buyurtmalar", callback_data="admin_orders"))
    return b.as_markup()

def get_admin_check_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Admin: Chekni tasdiqlash/rad etish"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_confirm_{order_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_reject_{order_id}")
    )
    return builder.as_markup()

def get_admin_categories_keyboard(categories: List[dict]) -> InlineKeyboardMarkup:
    """Admin: Kategoriya ro'yxati"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(
            InlineKeyboardButton(text=f"{category['emoji']} {category['name']}", callback_data=f"admin_cat_{category['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_cat_{category['id']}")
        )
    builder.row(InlineKeyboardButton(text="➕ Yangi kategoriya", callback_data="add_category"))
    return builder.as_markup()

def get_admin_products_keyboard(products: List[dict]) -> InlineKeyboardMarkup:
    """Admin: Mahsulot ro'yxati"""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(
            InlineKeyboardButton(text=f"📦 {product['name']}", callback_data=f"admin_prod_{product['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_prod_{product['id']}")
        )
    builder.row(InlineKeyboardButton(text="➕ Yangi mahsulot", callback_data="add_product"))
    return builder.as_markup()

def get_admin_select_category_keyboard(categories: List[dict]) -> InlineKeyboardMarkup:
    """Admin: Mahsulot qo'shish uchun kategoriya tanlash"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(InlineKeyboardButton(text=f"{category['emoji']} {category['name']}", callback_data=f"select_cat_{category['id']}"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_add_product"))
    return builder.as_markup()

def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Admin: Xabarni tasdiqlash"""
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Yuborish", callback_data="confirm_broadcast"), 
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
    )
    return b.as_markup()


# =========================================================
# 5. DO'KON TUGMALARI (FOYDALANUVCHI)
# =========================================================

def get_categories_keyboard(categories: List[dict]) -> InlineKeyboardMarkup:
    """Foydalanuvchi: Kategoriyalar"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"{category['emoji']} {category['name']}",
                callback_data=f"category_{category['id']}"
            )
        )
    return builder.as_markup()

def get_products_navigation(category_id: int, current_index: int, total: int, product_id: int) -> InlineKeyboardMarkup:
    """Mahsulotlarni varaqlash (User)"""
    builder = InlineKeyboardBuilder()
    
    # 1. Savatga qo'shish
    builder.row(InlineKeyboardButton(text="🛒 Savatga qo'shish", callback_data=f"add_cart_{product_id}"))
    
    # 2. Navigatsiya
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"prod_nav_{category_id}_{current_index - 1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="current_page"))
    
    if current_index < total - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"prod_nav_{category_id}_{current_index + 1}"))
    
    builder.row(*nav_buttons)
    
    # 3. Orqaga
    builder.row(InlineKeyboardButton(text="🔙 Kategoriyalarga", callback_data="back_to_categories"))
    return builder.as_markup()

def get_product_keyboard(product_id: int, in_cart: bool = False) -> InlineKeyboardMarkup:
    """Mahsulotni savatga qo'shish tugmasi"""
    builder = InlineKeyboardBuilder()
    if in_cart:
        builder.row(InlineKeyboardButton(text="✅ Savatda", callback_data=f"in_cart_{product_id}"))
    else:
        builder.row(InlineKeyboardButton(text="🛒 Savatga qo'shish", callback_data=f"add_cart_{product_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_categories"))
    return builder.as_markup()

def get_cart_keyboard(cart_items: List[dict]) -> InlineKeyboardMarkup:
    """Savatni boshqarish"""
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
    """Bo'sh savat tugmasi"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛍 Xarid qilish", callback_data="go_shopping"))
    return builder.as_markup()

def get_user_orders_navigation(current_index: int, total_orders: int) -> InlineKeyboardMarkup:
    """Mening buyurtmalarim navigatsiyasi"""
    builder = InlineKeyboardBuilder()
    buttons = []

    if current_index > 0:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"my_orders_prev_{current_index}"))

    buttons.append(InlineKeyboardButton(text=f"{current_index + 1} / {total_orders}", callback_data="noop"))

    if current_index < total_orders - 1:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"my_orders_next_{current_index}"))

    builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="❌ Yopish", callback_data="close_my_orders"))
    return builder.as_markup()

def get_confirm_order_keyboard() -> InlineKeyboardMarkup:
    """Buyurtmani tasdiqlash tugmasi (Savatdan)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")
    )
    return builder.as_markup()


# =========================================================
# 6. QO'SHIMCHA TUGMALAR (Limit, Sayt, Aloqa)
# =========================================================

def get_limit_keyboard() -> InlineKeyboardMarkup:
    """Limit olish (WebApp)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🚀 Limitni tekshirish", 
            web_app=WebAppInfo(url=NASIYA_URL) 
        )
    )
    return builder.as_markup()

def get_website_keyboard() -> InlineKeyboardMarkup:
    """Platformaga o'tish"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="↗️ Platformaga kirish", 
            url=PLATFORM_URL 
        )
    )
    return builder.as_markup()

def get_contact_keyboard() -> InlineKeyboardMarkup:
    """Aloqa tugmalari"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💬 Admin bilan bog'lanish", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"))
    builder.row(InlineKeyboardButton(text="✍️ Xabar qoldirish", callback_data="leave_feedback"))
    builder.row(InlineKeyboardButton(text="📍 Manzilimiz", callback_data="show_location"))
    return builder.as_markup()

def get_subscription_keyboard():
    """Majburiy obuna"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 1-Kanalga a'zo bo'lish", url="https://t.me/xitoybozor_n1"))
    builder.row(InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription"))
    return builder.as_markup()


# =========================================================
# 7. YORDAMCHI TUGMALAR (Cancel, Skip, Phone)
# =========================================================

def get_cancel_button() -> ReplyKeyboardMarkup:
    """Bekor qilish (Reply)"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)

def get_skip_button() -> ReplyKeyboardMarkup:
    """O'tkazib yuborish (Reply)"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭ O'tkazib yuborish"),
        KeyboardButton(text="❌ Bekor qilish")
    )
    return builder.as_markup(resize_keyboard=True)

def get_back_button() -> ReplyKeyboardMarkup:
    """Orqaga (Reply)"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🔙 Orqaga"))
    return builder.as_markup(resize_keyboard=True)

def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqam so'rash"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True))
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


# =========================================================
# 8. MAXSUS  SHOP 
# =========================================================

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.web_app_info import WebAppInfo

# Sening yangi Vercel sayting manzili
SHOP_URL = "https://ruslan-shop-brand-s8n3.vercel.app"

def get_buy_button(product_name: str, price: int) -> InlineKeyboardMarkup:
    """Universal WebApp Sotib olish Tugmasi"""
    # URL orqali saytga mahsulot nomi va narxini berib yuboramiz
    full_url = f"{SHOP_URL}?name={product_name}&price={price}"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛍 Sayt orqali sotib olish", 
            web_app=WebAppInfo(url=full_url)
        )
    )
    return builder.as_markup()

def get_clothing_keyboard() -> InlineKeyboardMarkup:
    """Jinsi va Bryuk uchun maxsus tugmalar (Ruslan Shop orqali)"""
    builder = InlineKeyboardBuilder()
    
    # 1. Oversize Jeans
    url_jeans = f"{SHOP_URL}?name=Oversize Jeans&price=170000"
    builder.row(
        InlineKeyboardButton(
            text="👖 Oversize Jeans - Sotib olish", 
            web_app=WebAppInfo(url=url_jeans)
        )
    )
    
    # 2. Oversize Bryuk
    url_bryuk = f"{SHOP_URL}?name=Oversize Bryuk&price=90000"
    builder.row(
        InlineKeyboardButton(
            text="👖 Oversize Bryuk - Sotib olish", 
            web_app=WebAppInfo(url=url_bryuk)
        )
    )
    
    return builder.as_markup()

def get_shop_keyboard():
    """Asosiy menyudagi Ruslan | Shop tugmasi bosilganda chiqadigan WebApp tugma"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🌐 Do'konga kirish (Web)", 
            web_app=WebAppInfo(url=SHOP_URL)
        )
    )
    return builder.as_markup()