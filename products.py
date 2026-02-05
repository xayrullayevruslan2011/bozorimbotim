"""
Mahsulotlar bo'limi handlerlari
Kategoriyalar va Mahsulotlarni ko'rish, varaqlash
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMediaVideo
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
        await message.answer("🤷‍♂️ Hozircha kategoriyalar mavjud emas. Admin panel orqali qo'shing.")
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
        await callback.answer("⚠️ Bu kategoriyada mahsulotlar yo'q.", show_alert=True)
        return

    # Birinchi mahsulotni ko'rsatamiz (index=0)
    await show_product_item(callback, products, 0, category_id)


async def show_product_item(callback: CallbackQuery, products: list, index: int, category_id: int):
    """Bitta mahsulotni chiroyli qilib ko'rsatish funksiyasi"""
    product = products[index]
    total = len(products)
    
    # Rasm yoki Video IDlarini ajratish
    media_ids = product['photo_id'].split(",") if product['photo_id'] else []
    main_media = media_ids[0] if media_ids else None
    
    text = (
        f"📦 <b>{product['name']}</b>\n\n"
        f"📝 <i>{product['description']}</i>\n\n"
        f"📏 <b>Razmer:</b> {product['size'] or 'Standard'}\n"
        f"📊 <b>Omborda:</b> {product['stock']} dona\n\n"
        f"💰 <b>Narxi:</b> {product['price']:,} so'm"
    )
    
    keyboard = get_products_navigation(category_id, index, total, product['id'])
    
    # Media turi va ID sini aniqlash (photo:ID formatidan tozalash)
    file_id = None
    media_type = "photo"
    
    if main_media:
        if ":" in main_media:
            media_type, file_id = main_media.split(":", 1)
        else:
            file_id = main_media
    
    try:
        if file_id:
            # Media obyektini yaratish
            if media_type == "video":
                media = InputMediaVideo(media=file_id, caption=text, parse_mode="HTML")
            else:
                media = InputMediaPhoto(media=file_id, caption=text, parse_mode="HTML")

            # Xabarni tahrirlash (agar rasm/video bo'lsa)
            if callback.message.photo or callback.message.video:
                await callback.message.edit_media(media=media, reply_markup=keyboard)
            else:
                # Agar oldingi xabar tekst bo'lsa, yangi yuboramiz
                await callback.message.delete()
                if media_type == "video":
                    await callback.message.answer_video(video=file_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    await callback.message.answer_photo(photo=file_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            # Rasmsiz mahsulot bo'lsa
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            
    except Exception:
        # Har qanday xatolikda yangidan yuborish (xavfsiz yo'l)
        await callback.message.delete()
        if file_id:
            if media_type == "video":
                await callback.message.answer_video(video=file_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await callback.message.answer_photo(photo=file_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
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
        
    if 0 <= new_index < len(products):
        await show_product_item(callback, products, new_index, category_id)
    else:
        await callback.answer("Boshqa mahsulot yo'q.", show_alert=False)


# =========================================================
# 4. SAVATGA QO'SHISH
# =========================================================

@router.callback_query(F.data.startswith("add_cart_"))
async def add_product_to_cart(callback: CallbackQuery):
    """Mahsulotni savatga qo'shish"""
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    await add_to_cart(user_id, product_id, 1)
    await callback.answer("✅ Savatga qo'shildi!", show_alert=True)