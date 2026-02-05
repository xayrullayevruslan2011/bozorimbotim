"""
Admin handlerlari (TO'LIQ VA KENGAYTIRILGAN VERSIYA)
Hamma funksiyalar joyida:
1. Kategoriyalar (Qo'shish/O'chirish)
2. Mahsulotlar (Razmer, Ko'p rasm, Stock, Narx, Tavsif)
3. Statistika
4. Xabar yuborish (Broadcast)
5. Buyurtmalar (Tasdiqlash/Rad etish)
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

# Config
from config import ADMIN_IDS

# Database importlari (Hamma kerakli funksiyalar)
from database import (
    get_categories, 
    add_category, 
    delete_category,
    get_all_products, 
    add_product, 
    delete_product, 
    get_all_users, 
    get_users_count, 
    update_order_status
)

# Keyboards va States importlari
from keyboards import (
    get_admin_panel_keyboard, 
    get_admin_categories_keyboard,
    get_admin_products_keyboard, 
    get_admin_select_category_keyboard,
    get_cancel_button, 
    get_skip_button, 
    get_broadcast_confirm_keyboard,
    get_main_menu
)
from states import AddProductState, AddCategoryState, BroadcastState, AdminState

router = Router()

# ============ YORDAMCHI TUGMALAR (Faqat Admin uchun shu yerda) ============

def get_size_keyboard():
    """Razmer tanlash uchun maxsus tugma"""
    kb = [
        [KeyboardButton(text="S"), KeyboardButton(text="M"), KeyboardButton(text="L")],
        [KeyboardButton(text="XL"), KeyboardButton(text="XXL"), KeyboardButton(text="3XL")],
        [KeyboardButton(text="36"), KeyboardButton(text="37"), KeyboardButton(text="38")],
        [KeyboardButton(text="39"), KeyboardButton(text="40"), KeyboardButton(text="41")],
        [KeyboardButton(text="Standard"), KeyboardButton(text="Razmersiz")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

def get_done_keyboard():
    """Rasm yuklashni tugatish tugmasi"""
    kb = [[KeyboardButton(text="✅ TAYYOR")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ============ ADMIN TEKSHIRUVI ============
def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshiradi"""
    return user_id in ADMIN_IDS


# ============ ADMIN PANEL MENYUSI ============
@router.message(F.text == "👨‍💼 Admin Panel")
async def admin_panel(message: Message):
    """Admin panelga kirish"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin huquqlari yo'q!")
        return
    
    await message.answer(
        "👨‍💼 <b>Admin Panel</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="HTML"
    )


# ============ 1. STATISTIKA BO'LIMI ============
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Statistikani ko'rsatish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    
    # Bazadan ma'lumotlarni olamiz
    users_count = await get_users_count()
    products = await get_all_products()
    categories = await get_categories()
    
    stats_text = f"""
📊 <b>Bot Statistikasi</b>

👥 Jami foydalanuvchilar: {users_count} ta
📦 Jami mahsulotlar: {len(products)} ta
📁 Jami kategoriyalar: {len(categories)} ta
"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ============ 2. KATEGORIYALAR BOSHQARUVI ============

@router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: CallbackQuery):
    """Kategoriyalar ro'yxatini ko'rsatish"""
    if not is_admin(callback.from_user.id): return
    
    categories = await get_categories()
    
    await callback.message.edit_text(
        "📁 <b>Kategoriyalar boshqaruvi</b>\n\n"
        "Kategoriyani tanlang yoki yangi qo'shing:",
        reply_markup=get_admin_categories_keyboard(categories),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "add_category")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    """Yangi kategoriya qo'shishni boshlash"""
    if not is_admin(callback.from_user.id): return
    
    await callback.message.delete()
    await callback.message.answer(
        "📁 <b>Yangi kategoriya qo'shish</b>\n\n"
        "Kategoriya nomini kiriting:",
        reply_markup=get_cancel_button()
    )
    await state.set_state(AddCategoryState.name)

@router.message(AddCategoryState.name)
async def process_category_name(message: Message, state: FSMContext):
    """Kategoriya nomini saqlash va emoji so'rash"""
    await state.update_data(name=message.text)
    
    await message.answer(
        "Kategoriya uchun emoji kiriting (masalan: 📦):\n"
        "Yoki o'tkazib yuborish tugmasini bosing.",
        reply_markup=get_skip_button()
    )
    await state.set_state(AddCategoryState.emoji)

@router.message(AddCategoryState.emoji)
async def process_category_emoji(message: Message, state: FSMContext):
    """Kategoriya emojisini saqlash va bazaga yozish"""
    if message.text == "⏭ O'tkazib yuborish":
        emoji = "📦"
    else:
        emoji = message.text
    
    data = await state.get_data()
    
    # Bazaga qo'shish
    await add_category(data['name'], emoji)
    
    await state.clear()
    await message.answer(
        f"✅ <b>Kategoriya muvaffaqiyatli qo'shildi!</b>\n\n"
        f"Nomi: {emoji} {data['name']}",
        reply_markup=get_main_menu(True),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("delete_cat_"))
async def delete_category_handler(callback: CallbackQuery):
    """Kategoriyani o'chirish"""
    if not is_admin(callback.from_user.id): return
    
    category_id = int(callback.data.split("_")[2])
    await delete_category(category_id)
    
    # Ro'yxatni yangilash
    categories = await get_categories()
    await callback.message.edit_text(
        "✅ Kategoriya o'chirildi.\n\n"
        "📁 <b>Kategoriyalar boshqaruvi:</b>",
        reply_markup=get_admin_categories_keyboard(categories),
        parse_mode="HTML"
    )


# ============ 3. MAHSULOTLAR BOSHQARUVI (TO'LIQ) ============

@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    """Mahsulotlar ro'yxatini ko'rsatish"""
    if not is_admin(callback.from_user.id): return
    
    products = await get_all_products()
    
    await callback.message.edit_text(
        "📦 <b>Mahsulotlar boshqaruvi</b>\n\n"
        f"Jami mahsulotlar: {len(products)} ta",
        reply_markup=get_admin_products_keyboard(products),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    """Mahsulot qo'shishni boshlash: Kategoriya tanlash"""
    if not is_admin(callback.from_user.id): return
    
    categories = await get_categories()
    if not categories:
        await callback.answer("❌ Avval kategoriya yarating!", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "📦 <b>Yangi mahsulot qo'shish</b>\n\n"
        "Qaysi kategoriyaga qo'shmoqchisiz?",
        reply_markup=get_admin_select_category_keyboard(categories),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.category)

@router.callback_query(AddProductState.category, F.data.startswith("select_cat_"))
async def select_product_category(callback: CallbackQuery, state: FSMContext):
    """Kategoriya tanlandi, endi Nomini so'raymiz"""
    category_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=category_id)
    
    await callback.message.delete()
    await callback.message.answer(
        "📝 <b>Mahsulot nomini kiriting:</b>",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.name)

@router.message(AddProductState.name)
async def process_product_name(message: Message, state: FSMContext):
    """Nomi olindi, endi Narxini so'raymiz"""
    await state.update_data(name=message.text)
    
    await message.answer(
        "💰 <b>Mahsulot narxini kiriting:</b>\n"
        "(Faqat raqam, masalan: 150000)",
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.price)

@router.message(AddProductState.price)
async def process_product_price(message: Message, state: FSMContext):
    """Narx olindi, endi RAZMER so'raymiz"""
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, faqat raqam kiriting!")
        return
    
    await state.update_data(price=int(message.text))
    
    # YANGI: Razmer so'rash qismi
    await message.answer(
        "📏 <b>Mahsulot razmerini tanlang yoki yozing:</b>\n"
        "(Kiyimlar: S, M... | Oyoq kiyim: 39, 40... | Yoki 'Razmersiz')",
        reply_markup=get_size_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.size)

@router.message(AddProductState.size)
async def process_product_size(message: Message, state: FSMContext):
    """Razmer olindi, endi Tavsif so'raymiz"""
    await state.update_data(size=message.text)
    
    await message.answer(
        "📝 <b>Mahsulot haqida ma'lumot (Description) yozing:</b>",
        reply_markup=ReplyKeyboardRemove(), # Razmer tugmalarini olib tashlaymiz
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.description)

@router.message(AddProductState.description)
async def process_product_description(message: Message, state: FSMContext):
    """Tavsif olindi, endi MEDIA (Rasm/Video) so'raymiz"""
    await state.update_data(description=message.text)
    
    await message.answer(
        "📸 <b>Mahsulot rasmi yoki videosini yuboring:</b>\n\n"
        "🔹 Bir nechta fayl yuborishingiz mumkin.\n"
        "🔹 Tugatish uchun <b>'✅ TAYYOR'</b> tugmasini bosing.",
        reply_markup=get_done_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.photo)

# --- MEDIA QABUL QILISH (KO'P RASM/VIDEO) ---
@router.message(AddProductState.photo, F.photo | F.video)
async def process_product_media(message: Message, state: FSMContext):
    """Har bir yuborilgan rasm/videoni ro'yxatga qo'shamiz"""
    data = await state.get_data()
    # Agar oldin rasm bo'lmasa, bo'sh ro'yxat yaratamiz
    m_list = data.get("media_list", [])
    
    if message.photo:
        # Eng sifatli rasmni olamiz
        file_id = f"photo:{message.photo[-1].file_id}"
        m_list.append(file_id)
    elif message.video:
        file_id = f"video:{message.video.file_id}"
        m_list.append(file_id)
    
    await state.update_data(media_list=m_list)
    
    await message.answer(
        f"✅ Fayl qabul qilindi! (Jami: {len(m_list)} ta)\n"
        "Yana yuboring yoki tugatish uchun <b>'✅ TAYYOR'</b> tugmasini bosing."
    )

# --- "✅ TAYYOR" BOSILGANDA ---
@router.message(AddProductState.photo, F.text == "✅ TAYYOR")
async def finish_media_upload(message: Message, state: FSMContext):
    """Media yuklash tugadi, endi STOCK (Soni) so'raymiz"""
    data = await state.get_data()
    m_list = data.get("media_list", [])
    
    if not m_list:
        await message.answer("⚠️ Iltimos, hech bo'lmasa bitta rasm yoki video yuboring!")
        return
    
    await message.answer(
        "📊 <b>Ombordagi mahsulot sonini kiriting (Stock):</b>\n"
        "(Masalan: 50)",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.stock)

@router.message(AddProductState.stock)
async def process_product_stock(message: Message, state: FSMContext):
    """Oxirgi qadam: Stock saqlanadi va mahsulot bazaga yoziladi"""
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    
    stock = int(message.text)
    data = await state.get_data()
    
    # Media ro'yxatini stringga aylantiramiz (vergul bilan)
    media_str = ",".join(data['media_list'])
    
    # BAZAGA YOZISH
    await add_product(
        category_id=data['category_id'],
        name=data['name'],
        description=data['description'],
        price=data['price'],
        size=data['size'],  # Yangi
        photo_id=media_str, # Yangi (ko'p rasm)
        stock=stock         # Yangi
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Mahsulot muvaffaqiyatli qo'shildi!</b>\n\n"
        f"📦 Nomi: {data['name']}\n"
        f"📏 Razmer: {data['size']}\n"
        f"💰 Narxi: {data['price']:,} so'm\n"
        f"📊 Soni: {stock} dona",
        reply_markup=get_main_menu(True),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("delete_prod_"))
async def delete_product_handler(callback: CallbackQuery):
    """Mahsulotni o'chirish"""
    if not is_admin(callback.from_user.id): return
    
    product_id = int(callback.data.split("_")[2])
    await delete_product(product_id)
    
    products = await get_all_products()
    await callback.message.edit_text(
        "✅ Mahsulot o'chirildi.\n\n"
        f"📦 Jami mahsulotlar: {len(products)} ta",
        reply_markup=get_admin_products_keyboard(products),
        parse_mode="HTML"
    )


# ============ 4. XABAR YUBORISH (BROADCAST) ============

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    
    await callback.message.edit_text(
        "📢 <b>Xabar yuborish</b>\n\n"
        "Xabar matnini kiriting:",
        parse_mode="HTML"
    )
    await callback.message.answer("Xabar matnini yozing:", reply_markup=get_cancel_button())
    await state.set_state(BroadcastState.message)

@router.message(BroadcastState.message)
async def broadcast_msg(message: Message, state: FSMContext):
    await state.update_data(msg=message.text)
    await message.answer(
        f"Tasdiqlaysizmi?\n\n{message.text}", 
        reply_markup=get_broadcast_confirm_keyboard()
    )
    await state.set_state(BroadcastState.confirm)

@router.callback_query(BroadcastState.confirm, F.data == "confirm_broadcast")
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_text = data['msg']
    users = await get_all_users()
    
    count = 0
    await callback.message.edit_text("⏳ Xabar yuborilmoqda...")
    
    for user_id in users:
        try:
            await callback.bot.send_message(user_id, f"📢 <b>YANGILIK:</b>\n\n{message_text}", parse_mode="HTML")
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
            
    await state.clear()
    await callback.message.answer(f"✅ Xabar {count} ta foydalanuvchiga yuborildi.", reply_markup=get_main_menu(True))

@router.callback_query(BroadcastState.confirm, F.data == "cancel_broadcast")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")


# ============ 5. BUYURTMALAR BOSHQARUVI ============

@router.callback_query(F.data == "admin_orders")
async def admin_orders_list(callback: CallbackQuery):
    """Buyurtmalar bo'limi"""
    await callback.answer(f"Yangi buyurtmalar sizga rasm shaklida keladi.", show_alert=True)

# TASDIQLASH (Confirm)
@router.callback_query(F.data.startswith("admin_confirm_"))
async def approve_order_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    
    order_id = callback.data.split("_")[2]
    
    await callback.message.answer(
        f"✅ <b>Buyurtma #{order_id} qabul qilindi.</b>\n\n"
        "✍️ Iltimos, mijozga yuborish uchun <b>TREK RAQAMNI</b> yozing:",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.update_data(order_id=order_id)
    await state.set_state(AdminState.waiting_for_track)
    await callback.answer()

@router.message(AdminState.waiting_for_track)
async def process_track_code(message: Message, state: FSMContext):
    """Trek kodni qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=get_main_menu(True))
        return

    track_code = message.text
    data = await state.get_data()
    order_id = data.get('order_id')
    
    # Bazada statusni yangilash
    await update_order_status(order_id, "confirmed")
    
    # TODO: Trek kodni bazaga yozish va userga xabar yuborish logikasi shu yerda bo'ladi
    
    await message.answer(
        f"✅ <b>Trek kod qabul qilindi:</b> {track_code}\n"
        f"Buyurtma #{order_id} tasdiqlandi.",
        reply_markup=get_main_menu(True),
        parse_mode="HTML"
    )
    await state.clear()

# RAD ETISH (Reject)
@router.callback_query(F.data.startswith("admin_reject_"))
async def reject_order_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    
    order_id = callback.data.split("_")[2]
    
    # Statusni yangilash
    await update_order_status(order_id, "cancelled")
    
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n❌ <b>RAD ETILDI</b>",
        reply_markup=None,
        parse_mode="HTML"
    )
    await callback.answer("❌ Buyurtma bekor qilindi")


# ============ UMUMIY BEKOR QILISH ============
@router.message(F.text == "❌ Bekor qilish")
@router.callback_query(F.data == "cancel_add_product")
async def cancel_all(obj, state: FSMContext):
    await state.clear()
    if isinstance(obj, Message):
        await obj.answer("❌ Jarayon bekor qilindi.", reply_markup=get_main_menu(True))
    else:
        await obj.message.delete()
        await obj.message.answer("❌ Jarayon bekor qilindi.", reply_markup=get_main_menu(True))