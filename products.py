"""
Mahsulotlar handlerlari
Kategoriyalar, mahsulotlarni ko'rish va RAZMER TANLASH (Kiyim + Oyoq kiyim)
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

# database dan kerakli funksiyalarni chaqiramiz
from database import (
    get_categories, 
    get_products_by_category,
    get_product,
    get_cart,
    add_to_cart
)
from keyboards import (
    get_categories_keyboard,
    get_products_navigation,
    get_main_menu,
    get_back_button
)
from config import ADMIN_IDS

router = Router()

@router.message(F.text == "🛍 Mahsulotlar")
async def show_categories(message: Message):
    """Kategoriyalarni ko'rsatish"""
    categories = await get_categories()
    
    if not categories:
        await message.answer(
            "😔 Hozircha kategoriyalar mavjud emas.",
            reply_markup=get_main_menu(message.from_user.id in ADMIN_IDS)
        )
        return
    
    await message.answer(
        "📁 <b>Kategoriyani tanlang:</b>",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Kategoriyalarga qaytish"""
    categories = await get_categories()
    
    await callback.message.edit_text(
        "📁 <b>Kategoriyani tanlang:</b>",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery):
    """Kategoriya mahsulotlarini ko'rsatish"""
    parts = callback.data.split("_")
    category_id = int(parts[1])
    
    products = await get_products_by_category(category_id)
    
    if not products:
        await callback.answer("😔 Bu kategoriyada mahsulotlar yo'q", show_alert=True)
        return
    
    # Birinchi mahsulotni ko'rsatish
    await show_product(callback, products, 0, category_id)
    await callback.answer()

async def show_product(callback: CallbackQuery, products: list, index: int, category_id: int):
    """Mahsulotni ko'rsatish"""
    product = products[index]
    total = len(products)
    
    product_text = f"""
📦 <b>{product['name']}</b>

📝 {product['description'] or 'Tavsif mavjud emas'}

💰 Narxi: <b>{product['price']:,} so'm</b>
📊 Mavjud: {product['stock']} dona
"""
    
    keyboard = get_products_navigation(
        category_id=category_id,
        current_index=index,
        total=total,
        product_id=product['id']
    )
    
    try:
        if product['photo_id']:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=product['photo_id'],
                caption=product_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                product_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    except Exception:
        try:
            await callback.message.edit_caption(caption=product_text, reply_markup=keyboard, parse_mode="HTML")
        except:
            pass # Xatolik bo'lsa indamaymiz

@router.callback_query(F.data.startswith("prod_nav_"))
async def navigate_products(callback: CallbackQuery):
    """Mahsulotlar bo'ylab harakatlanish"""
    parts = callback.data.split("_")
    category_id = int(parts[2])
    index = int(parts[3])
    
    products = await get_products_by_category(category_id)
    if products:
        await show_product(callback, products, index, category_id)
    await callback.answer()

@router.callback_query(F.data == "go_shopping")
async def go_shopping(callback: CallbackQuery):
    categories = await get_categories()
    await callback.message.answer(
        "📁 <b>Kategoriyani tanlang:</b>",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )
    await callback.answer()

# ==========================================
# 🔥 YANGI QO'SHILGAN: RAZMERLAR TIZIMI 🔥
# ==========================================

@router.callback_query(F.data.startswith("add_cart_"))
async def ask_product_size(callback: CallbackQuery):
    """Savatga qo'shishdan oldin razmer so'rash"""
    # callback.data masalan: "add_cart_15" bo'ladi
    product_id = int(callback.data.split("_")[2])
    
    # Razmer tugmalari
    clothing_sizes = ["S", "M", "L", "XL", "XXL"]
    shoe_sizes = ["38", "39", "40", "41", "42"]
    
    buttons = []
    # 1. Kiyim razmerlari (bir qatorda)
    row = []
    for size in clothing_sizes:
        row.append(InlineKeyboardButton(text=size, callback_data=f"size_{product_id}_{size}"))
    buttons.append(row)
    
    # 2. Poyabzal razmerlari (bir qatorda)
    row = []
    for size in shoe_sizes:
        row.append(InlineKeyboardButton(text=size, callback_data=f"size_{product_id}_{size}"))
    buttons.append(row)
    
    # 3. Bekor qilish
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="delete_msg")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        "📏 <b>Iltimos, razmerni tanlang:</b>\n"
        "<i>(Kiyimlar yoki Poyabzallar uchun)</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("size_"))
async def add_product_with_size(callback: CallbackQuery):
    """Razmer tanlangandan keyin savatga qo'shish"""
    parts = callback.data.split("_")
    product_id = int(parts[1])
    size = parts[2]
    
    # Bazaga qo'shamiz
    await add_to_cart(callback.from_user.id, product_id, 1)
    
    await callback.message.delete()
    await callback.answer(f"✅ {size}-razmer savatga qo'shildi!", show_alert=True)

@router.callback_query(F.data == "delete_msg")
async def delete_msg(callback: CallbackQuery):
    await callback.message.delete()
    
