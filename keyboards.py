"""
Foydalanuvchi handlerlari (TO'LIQ VERSIYA)
Barcha funksiyalar: Start, Kabinet, Kurslar, Savat, Buyurtmalar, Limit, Aloqa
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext

# Config
from config import ADMIN_IDS, ADMIN_USERNAME, REQUIRED_CHANNELS 

# DATABASE IMPORTLARI
from database import (
    add_user, 
    get_user, 
    get_user_balance, 
    get_referrals_count,
    add_order,          # Chek saqlash uchun
    get_user_orders,    # Buyurtmalar tarixi uchun
    get_top_referrals   # Top 10
)

# TUGMALAR
from keyboards import (
    get_main_menu, 
    get_contact_keyboard, 
    get_subscription_keyboard, 
    get_limit_keyboard,
    get_payment_cancel_keyboard,
    get_user_orders_navigation,
    get_admin_check_keyboard,
    get_tariffs_keyboard,           
    get_payment_actions_keyboard,
    get_cabinet_keyboard 
)
from states import ContactState, CheckoutState 

router = Router()

# Karta ma'lumotlari
CARD_NUMBER = "4073420067355457"
CARD_OWNER = "Holboyeva Gulzebo"


# ==================================================
# 1. OBUNA TEKSHIRISH
# ==================================================
async def check_sub_status(bot: Bot, user_id: int):
    """Foydalanuvchi kanallarga a'zo ekanligini tekshiradi"""
    if not REQUIRED_CHANNELS:
        return True

    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                return False
        except Exception:
            continue 
    return True


# ==================================================
# 2. START KOMANDASI
# ==================================================
@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext, bot: Bot):
    await state.clear()
    
    # Referal ID ni aniqlash
    args = command.args
    referrer_id = None
    if args and args.isdigit():
        if int(args) != message.from_user.id:
            referrer_id = int(args)

    # Bazaga qo'shish
    await add_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name,
        referrer_id=referrer_id
    )
    
    # Obuna tekshirish
    is_subscribed = await check_sub_status(bot, message.from_user.id)
    if not is_subscribed:
        await message.answer(
            f"👋 <b>Assalomu alaykum, {message.from_user.full_name}!</b>\n\n"
            "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_subscription_keyboard(),
            parse_mode="HTML"
        )
        return

    # Asosiy menyu
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        f"🛍 <b>Xush kelibsiz, {message.from_user.full_name}!</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_main_menu(is_admin),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "check_subscription")
async def check_btn(callback: CallbackQuery, bot: Bot):
    if await check_sub_status(bot, callback.from_user.id):
        await callback.message.delete()
        is_admin = callback.from_user.id in ADMIN_IDS
        await callback.message.answer(
            "✅ <b>Rahmat!</b> Botdan foydalanishingiz mumkin.", 
            reply_markup=get_main_menu(is_admin), 
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Hali a'zo bo'lmadingiz!", show_alert=True)


# ==================================================
# 🔥 YANGI BO'LIM (KABINET) 🔥
# ==================================================
@router.message(F.text == "📂 Yangi Bo'lim")
async def new_section_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    
    # Ma'lumotlarni olish
    user = await get_user(user_id)
    referrals = await get_referrals_count(user_id)
    
    if not user:
        await message.answer("⚠️ Ma'lumot topilmadi. /start ni bosing.")
        return

    # Formatlash
    balance = user.get('balance', 0)
    custom_id = user.get('custom_id', '----')
    reg_date = user.get('registered_at', 'Noma\'lum')
    
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    status = "Yangi 🐣"
    if referrals > 10: status = "Kumush 🥈"
    if referrals > 50: status = "Oltin 🥇"
    if referrals > 100: status = "VIP 🔥"

    text = (
        f"👤 <b>SHAXSIY KABINET</b>\n\n"
        f"🆔 <b>Mening ID:</b> <code>{custom_id}</code>\n"
        f"📅 <b>Sana:</b> {reg_date}\n\n"
        f"💰 <b>Balans:</b> {balance:,} so'm\n"
        f"👥 <b>Do'stlar:</b> {referrals} ta\n"
        f"🌟 <b>Status:</b> {status}\n\n"
        f"🔗 <b>Referal havola:</b>\n<code>{ref_link}</code>"
    )
    
    await message.answer(text, reply_markup=get_cabinet_keyboard(), parse_mode="HTML")

# --- KABINET TUGMALARI ---
@router.callback_query(F.data == "earn_money")
async def earn_money_handler(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    await callback.message.edit_text(
        f"💰 <b>PUL ISHLASH</b>\n\nDo'stlaringizga havolani yuboring va har bir odam uchun <b>50 so'm</b> oling!\n\n🔗 <code>{ref_link}</code>",
        reply_markup=get_cabinet_keyboard(), parse_mode="HTML"
    )

@router.callback_query(F.data == "withdraw_money")
async def withdraw_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    bal = await get_user_balance(user_id)
    if bal < 5000:
        await callback.answer(f"❌ Min. summa: 5000 so'm. Sizda: {bal} so'm", show_alert=True)
    else:
        await callback.answer("✅ So'rov adminga yuborildi!", show_alert=True)

@router.callback_query(F.data == "top_10")
async def top10_handler(callback: CallbackQuery):
    top_users = await get_top_referrals()
    if not top_users:
        await callback.answer("Hozircha reyting bo'sh.", show_alert=True)
        return
    text = "🏆 <b>TOP 10 FAOLLAR</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(top_users):
        prefix = medals[i] if i < 3 else f"{i+1}."
        text += f"{prefix} {u[0]} - {u[1]} ta\n"
    await callback.message.edit_text(text, reply_markup=get_cabinet_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "my_stats")
async def my_stats_handler(callback: CallbackQuery):
    await callback.answer("📊 Statistikangiz a'lo darajada!", show_alert=True)

@router.callback_query(F.data == "delete_message")
async def del_msg(callback: CallbackQuery):
    await callback.message.delete()


# ==================================================
# 🔥 ONLINE KURSLAR VA TO'LOV 🔥
# ==================================================
@router.message(F.text == "🎓 Online Kurslar")
async def show_courses(message: Message):
    text = "🎓 <b>XITOY SAVDO KURSLARI</b>\n\nTariflardan birini tanlang:"
    await message.answer(text, reply_markup=get_tariffs_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("tariff_"))
async def select_tariff(call: CallbackQuery, state: FSMContext):
    tariff = call.data.split("_")[1].upper()
    price = "50 000" if tariff == "START" else "70 000" if tariff == "PRO" else "100 000"
    
    await state.update_data(product_name=f"{tariff} Tarifi")
    await call.message.edit_text(
        f"Siz <b>{tariff}</b> tarifini tanladingiz.\nTo'lov summasi: <b>{price} so'm</b>\n\nQuyidagi karta raqamiga to'lov qiling va chekni yuboring:",
        reply_markup=get_payment_actions_keyboard(price),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "copy_card_number")
async def copy_card(call: CallbackQuery):
    await call.message.answer(f"<code>{CARD_NUMBER}</code>", parse_mode="HTML")
    await call.answer("Karta nusxalandi!")

@router.callback_query(F.data.startswith("copy_amount_"))
async def copy_amount_handler(call: CallbackQuery):
    amt = call.data.split("_")[2].replace(" ", "")
    await call.message.answer(f"<code>{amt}</code>", parse_mode="HTML")
    await call.answer("Summa nusxalandi!")

@router.callback_query(F.data == "check_payment")
async def check_payment_btn(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("📸 <b>Chek rasmini yuboring:</b>", reply_markup=get_payment_cancel_keyboard(), parse_mode="HTML")
    await state.set_state(CheckoutState.waiting_for_receipt)

# CHEK RASMINI QABUL QILISH
@router.message(CheckoutState.waiting_for_receipt, F.photo)
async def process_check_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    product_name = data.get("product_name", "Noma'lum to'lov")
    photo_id = message.photo[-1].file_id
    
    order_id = await add_order(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        photo_id=photo_id,
        product_name=product_name,
        status="pending"
    )
    
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("✅ <b>Chek qabul qilindi!</b>\nAdmin tez orada javob beradi.", reply_markup=get_main_menu(is_admin), parse_mode="HTML")
    await state.clear()
    
    # Adminga
    caption = f"🆕 <b>YANGI TO'LOV! #{order_id}</b>\n👤 {message.from_user.full_name}\n📦 {product_name}\n🆔 {message.from_user.id}"
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(admin_id, photo_id, caption=caption, reply_markup=get_admin_check_keyboard(order_id), parse_mode="HTML")
        except: pass

@router.message(CheckoutState.waiting_for_receipt, F.text == "❌ To'lovni bekor qilish")
async def cancel_checkout(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("❌ To'lov bekor qilindi.", reply_markup=get_main_menu(is_admin))


# ==================================================
# 🔥 MENING BUYURTMALARIM (YANGILANGAN) 🔥
# ==================================================
@router.message(F.text == "📦 Mening buyurtmalarim")
async def my_orders(message: Message):
    orders = await get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("🤷‍♂️ Sizda hali buyurtmalar yo'q.")
        return

    await show_order_item(message, orders, 0)

async def show_order_item(message, orders, index):
    order = orders[index] # (id, user_id, full_name, photo_id, product_name, status, track_code, created_at)
    
    txt = (
        f"📦 <b>Buyurtma #{order[0]}</b>\n"
        f"🛒 Mahsulot: {order[4]}\n"
        f"ℹ️ Holat: {order[5]}\n"
        f"🔢 Trek-kod: <code>{order[6] or 'Kutilmoqda...'}</code>"
    )
    
    kb = get_user_orders_navigation(index, len(orders))
    
    if isinstance(message, CallbackQuery):
        if order[3]:
            media = InputMediaPhoto(media=order[3], caption=txt, parse_mode="HTML")
            await message.message.edit_media(media, reply_markup=kb)
        else:
            await message.message.edit_text(txt, reply_markup=kb, parse_mode="HTML")
    else:
        if order[3]:
            await message.answer_photo(order[3], caption=txt, reply_markup=kb, parse_mode="HTML")
        else:
            await message.answer(txt, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("my_orders_"))
async def nav_orders(callback: CallbackQuery):
    action = callback.data.split("_")[2] # prev / next
    current_idx = int(callback.data.split("_")[3])
    
    orders = await get_user_orders(callback.from_user.id)
    if not orders: return await callback.answer()
    
    new_idx = current_idx - 1 if action == "prev" else current_idx + 1
    if 0 <= new_idx < len(orders):
        await show_order_item(callback, orders, new_idx)
    else:
        await callback.answer()

@router.callback_query(F.data == "close_my_orders")
async def close_orders(callback: CallbackQuery):
    await callback.message.delete()


# ==================================================
# QOLGANLAR (Limit, Aloqa, Ma'lumot)
# ==================================================
@router.message(F.text == "💰 Limit olish")
async def limit_handler(message: Message):
    await message.answer("🚀 <b>Limitni tekshirish:</b>", reply_markup=get_limit_keyboard(), parse_mode="HTML")

@router.message(F.text == "📞 Biz bilan aloqa")
async def contact_handler(message: Message):
    await message.answer("📞 Biz bilan bog'lanish:", reply_markup=get_contact_keyboard())

@router.callback_query(F.data == "leave_feedback")
async def feedback_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("✍️ Xabarni yozing:", parse_mode="HTML")
    await state.set_state(ContactState.message)

@router.message(ContactState.message)
async def feedback_msg(message: Message, state: FSMContext, bot: Bot):
    msg = f"📩 <b>YANGI XABAR!</b>\n👤 {message.from_user.full_name}\n💬 {message.text}"
    for uid in ADMIN_IDS:
        try: await bot.send_message(uid, msg, parse_mode="HTML")
        except: pass
    await state.clear()
    await message.answer("✅ Yuborildi!", reply_markup=get_main_menu(message.from_user.id in ADMIN_IDS))

@router.callback_query(F.data == "show_location")
async def show_loc(call: CallbackQuery):
    await call.message.answer_location(40.1031, 65.3742)
    await call.answer()

@router.message(F.text == "ℹ️ Ma'lumot")
async def info_handler(message: Message):
    await message.answer("ℹ️ <b>Ruslan|Market Bot</b>\nVersiya: 2.0 (Yangilangan)", parse_mode="HTML")

@router.message(F.text == "🔙 Orqaga")
@router.message(F.text == "❌ Bekor qilish")
async def back_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=get_main_menu(message.from_user.id in ADMIN_IDS))