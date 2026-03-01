"""
Admin handlerlari - TOZALANGAN VERSIYA
Faqat kerakli funksiyalar qoldirildi:
1. Statistika
2. Xabar yuborish (Broadcast)
3. Buyurtmalar (Tasdiqlash/Rad etish)
(Mahsulot va kategoriyalar WebApp ga o'tkazilgan)
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Config
from config import ADMIN_IDS

# Database importlari
from database import (
    get_categories, 
    get_all_products, 
    get_all_users, 
    get_users_count, 
    update_order_status
)

# Keyboards importlari (Faqat keraklilar qoldi, xato berganlari o'chirildi)
from keyboards import (
    get_admin_panel_keyboard, 
    get_cancel_button, 
    get_broadcast_confirm_keyboard,
    get_main_menu
)

# States (AddProduct va AddCategory o'chirildi, endi kerak emas)
from states import BroadcastState, AdminState

router = Router()


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
    
    # Xato bermasligi uchun try-except (Agar bazadagi mahsulotlarni o'chirib yuborsang bot o'chib qolmasligi uchun)
    try:
        products = await get_all_products()
        prod_count = len(products)
    except:
        prod_count = 0
        
    try:
        categories = await get_categories()
        cat_count = len(categories)
    except:
        cat_count = 0
    
    stats_text = f"""
📊 <b>Bot Statistikasi</b>

👥 Jami foydalanuvchilar: {users_count} ta
📦 Jami mahsulotlar: {prod_count} ta
📁 Jami kategoriyalar: {cat_count} ta
"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ============ 2. XABAR YUBORISH (BROADCAST) ============
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


# ============ 3. BUYURTMALAR BOSHQARUVI ============
@router.callback_query(F.data == "admin_orders")
async def admin_orders_list(callback: CallbackQuery):
    """Buyurtmalar bo'limi"""
    await callback.answer("Yangi buyurtmalar sizga rasm shaklida keladi.", show_alert=True)

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
    try:
        await update_order_status(order_id, "confirmed")
    except:
        pass
    
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
    try:
        await update_order_status(order_id, "cancelled")
    except:
        pass
    
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