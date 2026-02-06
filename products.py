"""
Mahsulotlar bo'limi handlerlari
Kategoriyalar, Mahsulotlarni ko'rish va Aqlli Qidiruv
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Database va Keyboards
from database import get_categories, get_products_by_category, add_to_cart, search_products
from keyboards import (
    get_categories_keyboard, 
    get_products_navigation, 
    get_main_menu
)

router = Router()

# Qidiruv uchun holat (State)
class SearchState(StatesGroup):
    waiting_for_query = State()

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
# 2. AQLLI QIDIRUV TIZIMI (YANGI)
# =========================================================

@router.message(F.text == "🔍 Qidiruv")
async def cmd_search(message: Message, state: FSMContext):
    """Qidiruvni boshlash"""
    await message.answer("🔎 Qidirayotgan mahsulot nomini yozing (masalan: <i>Oyoq kiyim</i>):", parse_mode="HTML")
    await state.set_state(SearchState.waiting_for_query)

@router.message(SearchState.waiting_for_query)
async def process_search(message: Message, state: FSMContext):
    """Qidiruv natijalarini ko'rsatish"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("⚠️ Iltimos, qidiruv uchun kamida 2 ta harf yozing.")
        return

    # Bazadan qidirish
    results = await search_products(query)
    
    if not results:
        await message.answer(f"🤷‍♂️ Afsuski, <b>'{query}'</b> bo'yicha hech narsa topilmadi.", parse_mode="HTML")
        await state.clear()
        return

    await message.answer(f"✅ <b>'{query}'</b> bo'yicha {len(results)} ta mahsulot topildi:")
    
    # Qidiruv natijasidagi birinchi mahsulotni ko'rsatamiz
    # Eslatma: Qidiruv natijasida navigatsiya (oldinga/orqaga) 
    # hozircha o'sha mahsulotning kategoriyasi bo'yicha ishlaydi.
    await show_product_item(message, results, 0, results[0]['category_id'])
    await state.clear()


# =========================================================
# 3. MAHSULOTLARNI KO'RSATISH (VARAQLASH)
# =========================================================

@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery):
    """Kategoriya ichidagi mahsulotlarni ochish"""
    category_id = int(callback.data.split("_")[1])
    products = await get_products_by_category(category_id)
    
    if not products:
        await callback.answer("⚠️ Bu kategoriyada mahsulotlar yo'q.", show_alert=True)
        return

    await show_product_item(callback, products, 0, category_id)


async def show_product_item(callback_or_message, products: list, index: int, category_id: int):
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
    
    # Media turi va ID sini aniqlash
    file_id = None
    media_type = "photo"
    
    if main_media:
        if ":" in main_media:
            media_type, file_id = main_media.split(":", 1)
        else:
            file_id = main_media
    
    # CallbackQuery yoki Message ekanligini aniqlash
    is_callback = isinstance(callback_or_message, CallbackQuery)
    message = callback_or_message.message if is_callback else callback_or_message

    try:
        if file_id:
            if media_type == "video":
                media = InputMediaVideo(media=file_id, caption=text, parse_mode="HTML")
            else:
                media = InputMediaPhoto(media=file_id, caption=text, parse_mode="HTML")

            if is_callback and (message.photo or message.video):
                await callback_or_message.message.edit_media(media=media, reply_markup=keyboard)
            else:
                if is_callback: await message.delete()
                if media_type == "video":
                    await message.answer_video(video=file_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    await message.answer_photo(photo=file_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            if is_callback:
                await callback_or_message.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            
    except Exception:
        if is_callback: await message.delete()
        if file_id:
            if media_type == "video":
                await message.answer_video(video=file_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await message.answer_photo(photo=file_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# =========================================================
# 4. NAVIGATSIYA (OLDINGA / ORQAGA)
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
# 5. SAVATGA QO'SHISH
# =========================================================

@router.callback_query(F.data.startswith("add_cart_"))
async def add_product_to_cart(callback: CallbackQuery):
    """Mahsulotni savatga qo'shish"""
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    await add_to_cart(user_id, product_id, 1)
    await callback.answer("✅ Savatga qo'shildi!", show_alert=True)