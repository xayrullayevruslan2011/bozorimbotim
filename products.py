"""
Mahsulotlar handlerlari
Kategoriyalar, mahsulotlarni ko'rish
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import (
    get_categories, 
    get_products_by_category,
    get_product,
    get_cart
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
async def show_category_products(callback: CallbackQuery, state: FSMContext):
    """Kategoriya mahsulotlarini ko'rsatish"""
    category_id = int(callback.data.split("_")[1])
    
    products = await get_products_by_category(category_id)
    
    if not products:
        await callback.answer("😔 Bu kategoriyada mahsulotlar yo'q", show_alert=True)
        return
    
    # Birinchi mahsulotni ko'rsatish
    await show_product(callback, products, 0, category_id)
    await callback.answer()


async def show_product(
    callback: CallbackQuery, 
    products: list, 
    index: int, 
    category_id: int
):
    """Mahsulotni ko'rsatish"""
    product = products[index]
    total = len(products)
    
    # Mahsulot matni
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
            # Rasm bilan
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=product['photo_id'],
                caption=product_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Rasmsiz
            await callback.message.edit_text(
                product_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    except Exception as e:
        # Xatolik bo'lsa matnni o'zgartirish
        try:
            await callback.message.edit_caption(
                caption=product_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except:
            await callback.message.edit_text(
                product_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )


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
    """Xarid qilishga o'tish"""
    categories = await get_categories()
    
    await callback.message.edit_text(
        "📁 <b>Kategoriyani tanlang:</b>",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )
    await callback.answer()
