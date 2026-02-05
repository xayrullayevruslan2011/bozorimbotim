"""
Mahsulotlar handlerlari
Kategoriyalar, mahsulotlarni ko'rish va KENGAYTIRILGAN RAZMER TANLASH (XS-5XL, 25-49)
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_categories, get_products_by_category, add_to_cart
from keyboards import get_categories_keyboard, get_products_navigation
from config import ADMIN_IDS

router = Router()

# ==========================================
# 1. KATEGORIYA VA MAHSULOTLARNI KO'RSATISH
# ==========================================

@router.message(F.text == "🛍 Mahsulotlar")
async def show_categories(message: Message):
    categories = await get_categories()
    if not categories:
        await message.answer("😔 Hozircha kategoriyalar mavjud emas.")
        return
    await message.answer("📁 <b>Kategoriyani tanlang:</b>", reply_markup=get_categories_keyboard(categories), parse_mode="HTML")

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    categories = await get_categories()
    await callback.message.edit_text("📁 <b>Kategoriyani tanlang:</b>", reply_markup=get_categories_keyboard(categories), parse_mode="HTML")

@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery):
    category_id = int(callback.data.split("_")[1])
    products = await get_products_by_category(category_id)
    if not products:
        await callback.answer("😔 Bu kategoriyada mahsulotlar yo'q", show_alert=True)
        return
    await show_product(callback, products, 0, category_id)

async def show_product(callback: CallbackQuery, products: list, index: int, category_id: int):
    product = products[index]
    total = len(products)
    
    text = (
        f"📦 <b>{product['name']}</b>\n\n"
        f"📝 {product['description'] or 'Tavsif yoq'}\n\n"
        f"💰 Narxi: <b>{product['price']:,} so'm</b>\n"
        f"📊 Omborda: {product['stock']} dona"
    )
    
    keyboard = get_products_navigation(category_id, index, total, product['id'])
    
    if product['photo_id']:
        await callback.message.delete()
        await callback.message.answer_photo(photo=product['photo_id'], caption=text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("prod_nav_"))
async def navigate_products(callback: CallbackQuery):
    parts = callback.data.split("_")
    category_id = int(parts[2])
    index = int(parts[3])
    products = await get_products_by_category(category_id)
    if products: await show_product(callback, products, index, category_id)


# ==========================================
# 🔥 YANGILANGAN: RAZMER TANLASH TIZIMI 🔥
# ==========================================

@router.callback_query(F.data.startswith("add_cart_"))
async def ask_product_size(callback: CallbackQuery):
    """Savatga qo'shishdan oldin razmer so'rash"""
    product_id = int(callback.data.split("_")[2])
    
    # 1. KIYIM RAZMERLARI (XS dan 5XL gacha)
    clothing_sizes = ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"]
    
    # 2. OYOQ KIYIM RAZMERLARI (25 dan 49 gacha)
    shoe_sizes = [str(i) for i in range(25, 50)] # 25, 26, ..., 49

    buttons = []
    
    # --- Kiyimlar sarlavhasi ---
    buttons.append([InlineKeyboardButton(text="👕 KIYIMLAR UCHUN:", callback_data="ignore")])
    
    # Kiyimlarni 5 tadan qatorga joylash
    row = []
    for size in clothing_sizes:
        row.append(InlineKeyboardButton(text=size, callback_data=f"size_{product_id}_{size}"))
        if len(row) == 5: 
            buttons.append(row)
            row = []
    if row: buttons.append(row)

    # --- Oyoq kiyimlar sarlavhasi ---
    buttons.append([InlineKeyboardButton(text="👟 OYOQ KIYIMLAR UCHUN:", callback_data="ignore")])
    
    # Oyoq kiyimlarni 5 tadan qatorga joylash
    row = []
    for size in shoe_sizes:
        row.append(InlineKeyboardButton(text=size, callback_data=f"size_{product_id}_{size}"))
        if len(row) == 5: 
            buttons.append(row)
            row = []
    if row: buttons.append(row)

    # Bekor qilish tugmasi
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="delete_msg")])
    
    await callback.message.answer(
        "📏 <b>Iltimos, o'lchamni tanlang:</b>\n"
        "<i>Mahsulot turiga qarab mos razmerni bosing 👇</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("size_"))
async def add_product_with_size(callback: CallbackQuery):
    """Razmer tanlangandan keyin savatga qo'shish"""
    parts = callback.data.split("_")
    product_id = int(parts[1])
    size = parts[2]
    
    # Mahsulotni savatga qo'shish
    await add_to_cart(callback.from_user.id, product_id, 1)
    
    await callback.message.delete()
    await callback.answer(f"✅ {size}-razmer tanlandi va savatga qo'shildi!", show_alert=True)

@router.callback_query(F.data == "delete_msg")
async def delete_msg(callback: CallbackQuery):
    await callback.message.delete()
    
@router.callback_query(F.data == "ignore")
async def ignore_click(callback: CallbackQuery):
    await callback.answer()