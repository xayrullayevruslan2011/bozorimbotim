"""
Mahsulotlar bo'limi handlerlari
Kategoriyalar va Mahsulotlarni ko'rish, varaqlash
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

# Database va Keyboards
from database import get_categories, get_products_by_category, add_to_cart
from keyboards import (
    get_categories_keyboard, 
    get_products_navigation, 
    get_main_menu
)

router = Router()

# =========================================================
# 1. KATEGORIYALARNI KO'RSATISH
# =========================================================

@router.message(F.text == "🛍 Mahsulotlar")
async def show_categories(message: Message):
    """Kategoriyalar ro'yxatini chiqarish"""
    categories = await get_categories()
    
    if not categories:
        await message.answer("🤷‍♂️ Hozircha kategoriyalar mavjud emas.")
        return

    await message.answer(
        "📂 <b>Kategoriyani tanlang:</b>",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_categories")
async def back_to_cats(callback: CallbackQuery):
    """Mahsulotdan orqaga qaytish"""
    await callback.message.delete()
    categories = await get_categories()
    await callback.message.answer(
        "📂 <b>Kategoriyani tanlang:</b>",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )


# =========================================================
# 2. MAHSULOTLARNI KO'RSATISH (VARAQLASH)
# =========================================================

@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery):
    """Kategoriya ichidagi mahsulotlarni ochish"""
    category_id = int(callback.data.split("_")[1])
    
    # Bazadan shu kategoriyadagi mahsulotlarni olamiz
    products = await get_products_by_category(category_id)
    
    if not products:
        await callback.answer("Bu kategoriyada mahsulotlar yo'q.", show_alert=True)
        return

    # Birinchi mahsulotni ko'rsatamiz (index=0)
    await show_product_item(callback, products, 0, category_id)


async def show_product_item(callback: CallbackQuery, products: list, index: int, category_id: int):
    """Bitta mahsulotni chiroyli qilib ko'rsatish funksiyasi"""
    product = products[index]
    total = len(products)
    
    # Mahsulot ma'lumotlari
    # product dict: {id, name, price, description, photo_id, size, stock, ...}
    
    # Rasm ID larini ajratib olish (agar vergul bilan ko'p rasm bo'lsa)
    photos = product['photo_id'].split(",") if product['photo_id'] else []
    main_photo = photos[0] if photos else None # Asosiy rasm
    
    text = (
        f"📦 <b>{product['name']}</b>\n\n"
        f"📝 <i>{product['description']}</i>\n\n"
        f"📏 <b>Razmer:</b> {product['size'] or 'Standard'}\n"
        f"📊 <b>Omborda:</b> {product['stock']} dona\n\n"
        f"💰 <b>Narxi:</b> {product['price']:,} so'm"
    )
    
    # Tugmalar (Savatga qo'shish va Oldinga/Orqaga)
    keyboard = get_products_navigation(category_id, index, total, product['id'])
    
    # Xabarni yangilash (Edit)
    try:
        if main_photo:
            # Agar oldingi xabar rasm bo'lsa -> EditMedia
            if callback.message.photo:
                media = InputMediaPhoto(media=main_photo, caption=text, parse_mode="HTML")
                await callback.message.edit_media(media=media, reply_markup=keyboard)
            # Agar oldingi xabar tekst bo'lsa (Kategoriyalar) -> Delete & Send Photo
            else:
                await callback.message.delete()
                await callback.message.answer_photo(photo=main_photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            # Rasmsiz mahsulot
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        # Xatolik bo'lsa yangi xabar yuboramiz (xavfsizlik uchun)
        await callback.message.delete()
        if main_photo:
            await callback.message.answer_photo(photo=main_photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# =========================================================
# 3. NAVIGATSIYA (OLDINGA / ORQAGA)
# =========================================================

@router.callback_query(F.data.startswith("prod_nav_"))
async def navigate_products(callback: CallbackQuery):
    """Keyingi yoki oldingi mahsulotga o'tish"""
    data = callback.data.split("_")
    category_id = int(data[2])
    new_index = int(data[3])
    
    products = await get_products_by_category(category_id)
    if not products:
        await callback.answer("Mahsulotlar topilmadi.")
        return
        
    # Indeks chegarasini tekshirish
    if 0 <= new_index < len(products):
        await show_product_item(callback, products, new_index, category_id)
    else:
        await callback.answer("Boshqa mahsulot yo'q.")


# =========================================================
# 4. SAVATGA QO'SHISH
# =========================================================

@router.callback_query(F.data.startswith("add_cart_"))
async def add_product_to_cart(callback: CallbackQuery):
    """Mahsulotni savatga qo'shish"""
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Bazaga qo'shish
    await add_to_cart(user_id, product_id, 1)
    
    await callback.answer("✅ Savatga qo'shildi!", show_alert=True)