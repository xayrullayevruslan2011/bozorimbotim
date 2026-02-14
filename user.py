"""
Foydalanuvchi handlerlari (TO'LIQ VA KENGAYTIRILGAN)
Eski 'db' olib tashlandi -> Yangi 'database.py' ga ulandi.
Barcha funksiyalar:
1. Start va Majburiy obuna
2. Yangi Kabinet (ID, Sana, Statistika)
3. Online Kurslar va To'lov (Chek yuborish)
4. Mening buyurtmalarim (Tarix)
5. Aloqa va Limitlar
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext

# Config ma'lumotlari
from config import ADMIN_IDS, ADMIN_USERNAME, REQUIRED_CHANNELS 

# DATABASE IMPORTLARI (Faqat 'database.py' dan)
from database import (
    add_user, 
    get_user, 
    get_user_balance, 
    get_referrals_count,
    add_order,          # Chek saqlash uchun
    get_user_orders,    # Buyurtmalar tarixi uchun
    get_top_referrals   # Top 10 talik uchun
)

# KLAVIATURALAR (TUGMALAR)
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
    get_cabinet_keyboard # Yangi kabinet tugmalari
)
from states import ContactState, CheckoutState 

router = Router()

# Karta ma'lumotlari (To'lov uchun)
CARD_NUMBER = "4073420067355457"
CARD_OWNER = "Holboyeva Gulzebo"


# ==================================================
# 1. OBUNA TEKSHIRISH (HELPER FUNCTION)
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
        except Exception as e:
            # Xatolikni konsolga chiqarish foydali (masalan, bot kanalda admin bo'lmasa)
            print(f"Kanal obunasini tekshirishda xatolik ({channel}): {e}")
            return False 
    return True


# ==================================================
# 2. START KOMANDASI
# ==================================================
@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext, bot: Bot):
    """Botni ishga tushirish"""
    await state.clear()
    
    # Referal ID ni aniqlash
    args = command.args
    referrer_id = None
    
    if args and args.isdigit():
        potential_referrer = int(args)
        if potential_referrer != message.from_user.id:
            referrer_id = potential_referrer

    # Foydalanuvchini bazaga qo'shish
    await add_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name,
        referrer_id=referrer_id
    )
    
    # Obunani tekshirish
    is_subscribed = await check_sub_status(bot, message.from_user.id)
    
    if not is_subscribed:
        await message.answer(
            f"👋 <b>Assalomu alaykum, {message.from_user.full_name}!</b>\n\n"
            "Botdan to'liq foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_subscription_keyboard(),
            parse_mode="HTML"
        )
        return

    # Agar a'zo bo'lsa, menyuni ochamiz
    is_admin = message.from_user.id in ADMIN_IDS
    
    welcome_text = f"""
🛍 <b>Ruslan|Market</b> ga xush kelibsiz!

Assalomu alaykum, <b>{message.from_user.full_name}</b>! 

Bu yerda siz turli xil mahsulotlarni ko'rishingiz, xarid qilishingiz va pul ishlashingiz mumkin.

📱 Quyidagi tugmalardan birini tanlang:
"""
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(is_admin),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "check_subscription")
async def check_btn(callback: CallbackQuery, bot: Bot):
    """Obunani tekshirish tugmasi"""
    is_subscribed = await check_sub_status(bot, callback.from_user.id)
    
    if is_subscribed:
        await callback.message.delete()
        is_admin = callback.from_user.id in ADMIN_IDS
        await callback.message.answer(
            "✅ <b>Rahmat! Siz barcha kanallarga a'zo bo'ldingiz.</b>\n\n"
            "Marhamat, xizmatlardan foydalanishingiz mumkin:",
            reply_markup=get_main_menu(is_admin),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Hali to'liq a'zo bo'lmadingiz! Iltimos, barcha kanallarga qo'shiling.", show_alert=True)
# ==================================================
# 🔥 YANGI BO'LIM (SHAXSIY KABINET) 🔥
# ==================================================
@router.message(F.text == "📂 Yangi Bo'lim")
async def new_section_handler(message: Message, bot: Bot):
    """Kabinetni ko'rsatish"""
    user_id = message.from_user.id
    
    # Bazadan ma'lumotlarni olamiz
    user = await get_user(user_id)
    referrals = await get_referrals_count(user_id)
    
    if not user:
        await message.answer("⚠️ Ma'lumot topilmadi. Qaytadan /start ni bosing.")
        return

    # Ma'lumotlarni formatlash
    balance = user.get('balance', 0)
    custom_id = user.get('custom_id', '----')
    reg_date = user.get('registered_at', 'Noma\'lum')
    
    # Referal havola
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    # Statusni aniqlash (daraja)
    status = "Yangi 🐣"
    if referrals > 10: status = "Kumush 🥈"
    if referrals > 50: status = "Oltin 🥇"
    if referrals > 100: status = "VIP 🔥"

    text = (
        f"👤 <b>SHAXSIY KABINET</b>\n\n"
        f"🆔 <b>Mening ID:</b> <code>{custom_id}</code>\n"
        f"📅 <b>Ro'yxatdan o'tgan sana:</b> {reg_date}\n\n"
        f"💰 <b>Balans:</b> {balance:,} so'm\n"
        f"👥 <b>Taklif qilinganlar:</b> {referrals} ta\n"
        f"🌟 <b>Status:</b> {status}\n\n"
        f"🔗 <b>Sizning referal havolangiz:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"<i>👆 Bu havolani do'stlaringizga yuboring. Har bir taklif uchun <b>50 so'm</b> oling!</i>"
    )
    
    # Yangi kabinet tugmalari (Pul ishlash, TOP 10, va h.k.)
    await message.answer(text, reply_markup=get_cabinet_keyboard(), parse_mode="HTML")


# --- KABINET TUGMALARI UCHUN HANDLERLAR ---

@router.callback_query(F.data == "earn_money")
async def earn_money_handler(callback: CallbackQuery, bot: Bot):
    """Pul ishlash bo'limi"""
    user_id = callback.from_user.id
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    await callback.message.edit_text(
        f"💰 <b>PUL ISHLASH</b>\n\n"
        f"Siz har bir taklif qilgan do'stingiz uchun <b>50 so'm</b> bonus olasiz.\n\n"
        f"🔗 <b>Havolangiz:</b>\n<code>{ref_link}</code>\n\n"
        f"Do'stlaringizga ulashing va pul ishlang!",
        reply_markup=get_cabinet_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "withdraw_money")
async def withdraw_money_handler(callback: CallbackQuery):
    """Pul yechish tugmasi"""
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    MIN_WITHDRAW = 5000  # Minimal summa
    
    if balance < MIN_WITHDRAW:
        await callback.answer(
            f"❌ Hisobingizda yetarli mablag' yo'q!\n\nMinimal yechish summasi: {MIN_WITHDRAW} so'm.\nSizda: {balance} so'm", 
            show_alert=True
        )
    else:
        await callback.answer("✅ So'rovingiz qabul qilindi! Admin tez orada aloqaga chiqadi.", show_alert=True)
        # Bu yerda adminga xabar yuborish funksiyasini qo'shish mumkin

@router.callback_query(F.data == "my_stats")
async def my_stats_handler(callback: CallbackQuery):
    """Statistika tugmasi"""
    user_id = callback.from_user.id
    referrals = await get_referrals_count(user_id)
    
    await callback.answer(
        f"📊 Siz jami {referrals} ta do'stingizni taklif qildingiz.\nFaolligingiz uchun rahmat! 😊", 
        show_alert=True
    )

@router.callback_query(F.data == "top_10")
async def top_10_handler(callback: CallbackQuery):
    """TOP 10 Reyting"""
    # Bazadan TOP 10 ni olamiz
    top_users = await get_top_referrals()
    
    if not top_users:
        await callback.answer("Hozircha reyting bo'sh.", show_alert=True)
        return

    text = "🏆 <b>TOP 10 FAOLLAR REYTINGI</b>\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, user in enumerate(top_users):
        name = user[0] # full_name
        count = user[1] # referral_count
        
        prefix = medals[i] if i < 3 else f"{i+1}."
        text += f"{prefix} <b>{name}</b> — {count} ta\n"
        
    await callback.message.edit_text(text, reply_markup=get_cabinet_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "exchange_money")
async def exchange_money_handler(callback: CallbackQuery):
    """Mahsulotga almashtirish"""
    await callback.answer("🎁 Tez orada bu yerda ballaringizga mahsulot olishingiz mumkin bo'ladi!", show_alert=True)

@router.callback_query(F.data == "delete_message")
async def delete_msg_handler(callback: CallbackQuery):
    """Xabarni o'chirish"""
    await callback.message.delete()


# ==================================================
# 🔥 ONLINE KURSLAR VA TO'LOV TIZIMI 🔥
# ==================================================

@router.message(F.text == "🎓 Online Kurslar")
async def show_courses_handler(message: Message):
    """Kurslar menyusini ko'rsatish"""
    text = (
        "👋 SALOM, QADRLI DO‘ST! 🤝\n\n"
        "🇨🇳 XITOY SAVDO KURSIMIZ 3 ta qulay tarif asosida o‘rgatiladi 👇\n\n"
        "———————————\n"
        "🔵 START TARIFI\n✅ Oyiga: 50 000 so‘m\n\n"
        "Ichida:\n"
        "✔️ Xitoydan olib kelish asoslari\n"
        "✔️ Kargo va narx hisoblash\n"
        "✔️ Boshlovchilar uchun yo‘l xarita\n\n"
        "———————————\n"
        "🟠 PRO TARIFI\n✅ Oyiga: 70 000 so‘m\n\n"
        "Ichida:\n"
        "✔️ Start tarifdagi hamma darslar\n"
        "✔️ Pinduoduo / 1688 bilan ishlash\n"
        "✔️ Arzon mahsulot topish usullari\n"
        "✔️ Xatolardan saqlanish\n\n"
        "———————————\n"
        "🟣 VIP TARIFI\n✅ Oyiga: 100 000 so‘m\n\n"
        "Ichida:\n"
        "✔️ BARCHA darslar\n"
        "✔️ WeChat orqali Xitoy sotuvchisi bilan yozishish\n"
        "✔️ Tayyor Xitoycha iboralar\n"
        "✔️ Real savdo misollar\n"
        "✔️ Yopiq Telegram guruh\n\n"
        "———————————\n"
        "⏳ JOYI CHEKLANGAN!\n"
        "Bugun qo‘shilmasangiz, keyin kech bo‘lishi mumkin ❗️\n"
        "🏃‍♂️ Shoshiling!"
    )
    await message.answer(text, reply_markup=get_tariffs_keyboard())


@router.callback_query(F.data.startswith("tariff_"))
async def select_tariff_handler(call: CallbackQuery, state: FSMContext):
    """Tarif tanlanganda"""
    tariff_code = call.data.split("_")[1]
    
    price = "0"
    tariff_name = ""
    
    if tariff_code == "start":
        price = "50 000"
        tariff_name = "🔵 START TARIFI"
    elif tariff_code == "pro":
        price = "70 000"
        tariff_name = "🟠 PRO TARIFI"
    elif tariff_code == "vip":
        price = "100 000"
        tariff_name = "🟣 VIP TARIFI"

    # State ga yozamiz
    await state.update_data(product_name=f"Online Kurs: {tariff_name}")

    text = (
        f"Siz tanladingiz: <b>{tariff_name}</b>\n\n"
        f"💳 <b>TO‘LOV QILISH UCHUN 👇</b>\n\n"
        f"👉 PAYME\n👉 CLICK\n👉 PAYNET\n\n"
        f"📌 Iltimos To’lov qilgandan keyin Chekni yuboring\n\n"
        f"💳 <b>Karta orqali:</b>\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"👤 <b>{CARD_OWNER}</b>\n\n"
        f"💰 <b>To'lov summasi:</b> {price} so'm"
    )

    await call.message.delete()
    await call.message.answer(text, parse_mode="HTML", reply_markup=get_payment_actions_keyboard(price))


@router.callback_query(F.data == "copy_card_number")
async def copy_card_handler(call: CallbackQuery):
    """Karta raqamini nusxalash"""
    await call.message.answer(f"<code>{CARD_NUMBER}</code>", parse_mode="HTML")
    await call.answer("Karta raqami yuborildi!", show_alert=True)


@router.callback_query(F.data.startswith("copy_amount_"))
async def copy_amount_handler(call: CallbackQuery):
    """Summani nusxalash"""
    amount = call.data.split("_")[2]
    clean_amount = amount.replace(" ", "")
    await call.message.answer(f"<code>{clean_amount}</code>", parse_mode="HTML")
    await call.answer(f"Summa ({clean_amount}) nusxalash uchun yuborildi!", show_alert=True)


@router.callback_query(F.data == "check_payment")
async def check_payment_handler(call: CallbackQuery, state: FSMContext):
    """To'lovni tekshirish (Rasm so'rash)"""
    await call.message.delete()
    await state.set_state(CheckoutState.waiting_for_receipt)
    
    await call.message.answer(
        "📸 <b>Iltimos, to'lov chekini rasm qilib yuboring.</b>",
        reply_markup=get_payment_cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(CheckoutState.waiting_for_receipt, F.photo)
async def process_receipt(message: Message, state: FSMContext, bot: Bot):
    """Chek rasmini qabul qilish va saqlash"""
    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    # State dan ma'lumotni olamiz
    data = await state.get_data()
    product_name = data.get("product_name", "Noma'lum to'lov")

    # Bazaga yozamiz (add_order funksiyasi orqali)
    order_id = await add_order(
        user_id=user_id, 
        full_name=full_name, 
        photo_id=photo_id, 
        product_name=product_name, 
        status="pending"
    )
    
    # Foydalanuvchiga javob
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        "✅ <b>To'lov cheki qabul qilindi!</b>\n\nAdmin tekshirib, tez orada javob beradi.", 
        reply_markup=get_main_menu(is_admin),
        parse_mode="HTML"
    )
    await state.clear()

    # Adminga xabar yuborish
    caption = (
        f"🆕 <b>Yangi to'lov!</b> #{order_id}\n"
        f"👤 Mijoz: {full_name}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🛍 Buyurtma: <b>{product_name}</b>\n"
        f"📝 Holat: Tekshirilmoqda..."
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_admin_check_keyboard(order_id)
            )
        except Exception:
            pass


@router.message(CheckoutState.waiting_for_receipt, F.text == "❌ To'lovni bekor qilish")
async def cancel_checkout(message: Message, state: FSMContext):
    """To'lovni bekor qilish"""
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("❌ To'lov bekor qilindi.", reply_markup=get_main_menu(is_admin))


# ==================================================
# 🔥 MENING BUYURTMALARIM (TARIX) 🔥
# ==================================================
@router.message(F.text == "📦 Mening buyurtmalarim")
async def show_my_orders(message: Message):
    """Buyurtmalar tarixini ko'rsatish"""
    # Bazadan shu odamning buyurtmalarini olamiz
    orders = await get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("🤷‍♂️ Sizda hali buyurtmalar yo'q.")
        return

    # Birinchi (eng oxirgi) buyurtmani ko'rsatamiz
    current_index = 0
    await show_order_item(message, orders, current_index)


async def show_order_item(message, orders, index):
    """Bitta buyurtmani ko'rsatish funksiyasi"""
    order = orders[index]
    total_orders = len(orders)
    
    # Bazadagi ustunlar tartibi: (id, user_id, full_name, photo_id, product_name, status, track_code, created_at)
    # order[0] -> id
    # order[3] -> photo_id
    # order[4] -> product_name
    # order[5] -> status
    # order[6] -> track_code
    
    status_text = order[5]
    if status_text == "confirmed": status_text = "✅ Tasdiqlangan"
    elif status_text == "cancelled": status_text = "❌ Bekor qilingan"
    elif status_text == "pending": status_text = "⏳ Kutilmoqda"

    track = order[6] if order[6] else "Hali berilmagan"

    caption = (
        f"📦 <b>Buyurtma #{order[0]}</b>\n"
        f"🛍 Mahsulot: {order[4]}\n"
        f"ℹ️ Holat: {status_text}\n"
        f"🔢 <b>Trek raqam:</b> <code>{track}</code>\n"
        f"📅 Sana: {order[7]}"
    )
    
    keyboard = get_user_orders_navigation(index, total_orders)
    
    # Rasm bilan chiqarish
    if isinstance(message, CallbackQuery):
        if order[3]:
            media = InputMediaPhoto(media=order[3], caption=caption, parse_mode="HTML")
            await message.message.edit_media(media=media, reply_markup=keyboard)
        else:
            await message.message.edit_text(caption, reply_markup=keyboard, parse_mode="HTML")
    else:
        if order[3]:
            await message.answer_photo(photo=order[3], caption=caption, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(caption, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("my_orders_"))
async def navigate_orders(callback: CallbackQuery):
    """Buyurtmalarni varaqlash"""
    action = callback.data.split("_")[2] # prev yoki next
    current_index = int(callback.data.split("_")[3])
    
    orders = await get_user_orders(callback.from_user.id)
    if not orders:
        await callback.answer("Buyurtmalar topilmadi")
        return

    # Indeksni hisoblash
    if action == "prev":
        new_index = max(0, current_index - 1)
    elif action == "next":
        new_index = min(len(orders) - 1, current_index + 1)
    else:
        new_index = current_index

    if new_index == current_index:
        await callback.answer()
        return

    await show_order_item(callback, orders, new_index)


@router.callback_query(F.data == "close_my_orders")
async def close_orders_window(callback: CallbackQuery):
    await callback.message.delete()


# ==================================================
# QOLGAN HANDLERLAR
# ==================================================

# user.py ichida
from keyboards import get_shop_keyboard # TEPAGA SHU IMPORTNI QO'SHISHNI UNUTMA!

@router.message(F.text == "🛍 Ruslan | Shop")
async def shop_handler(message: Message):
    text = (
        "<b>🛍 RUSLAN | SHOP</b>\n\n"
        "Internet-do'konimizga xush kelibsiz! Marhamat, pastdagi tugmani bosib tovarlar katalogi va o'z yuklaringizni (Trek-kodlarni) kuzating 👇"
    )
    await message.answer(text, reply_markup=get_shop_keyboard(), parse_mode="HTML")
@router.message(F.text == "🔙 Orqaga")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("🏠 Asosiy menyu", reply_markup=get_main_menu(is_admin))

@router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("❌ Bekor qilindi. Asosiy menyu:", reply_markup=get_main_menu(is_admin))

@router.message(F.text == "ℹ️ Ma'lumot")
async def show_info(message: Message):
    info_text = f"""
ℹ️ <b>Ruslan|Market Bot haqida</b>

🛍 Bu bot orqali siz quyidagilarni amalga oshirishingiz mumkin:
✅ Mahsulotlarni ko'rish va tanlash
✅ Savatga qo'shish
✅ Buyurtma berish
✅ Admin bilan bog'lanish

📞 Murojaat uchun: {ADMIN_USERNAME}
🔄 Bot versiyasi: 2.0 (To'liq yangilangan)
"""
    await message.answer(info_text, parse_mode="HTML")

@router.message(F.text == "⚙️ Sozlamalar")
async def show_settings(message: Message):
    user = await get_user(message.from_user.id)
    settings_text = f"""
⚙️ <b>Sozlamalar</b>
👤 <b>Sizning ma'lumotlaringiz:</b>
🆔 ID: <code>{message.from_user.id}</code>
👤 Ism: {message.from_user.full_name}
📧 Username: @{message.from_user.username or "yo'q"}
📅 Ro'yxatdan o'tgan: {user.get('registered_at', "Noma'lum") if user else "Noma'lum"}
"""
    await message.answer(settings_text, parse_mode="HTML")

@router.message(F.text == "📞 Biz bilan aloqa")
async def contact_us(message: Message):
    contact_text = f"""
📞 <b>Biz bilan aloqa</b>
Savollaringiz yoki takliflaringiz bo'lsa, biz bilan bog'lanishingiz mumkin:
👨‍💼 Admin: {ADMIN_USERNAME}
📍 Manzil: Navoiy shaxri
🕐 Ish vaqti: 09:00 - 18:00
"""
    await message.answer(contact_text, reply_markup=get_contact_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "leave_feedback")
async def leave_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍️ <b>Xabaringizni yozing:</b>\nSizning xabaringiz adminga yuboriladi.", parse_mode="HTML")
    await state.set_state(ContactState.message)

@router.message(ContactState.message)
async def process_feedback(message: Message, state: FSMContext):
    bot: Bot = message.bot
    feedback_text = f"📩 <b>Yangi xabar!</b>\n\n👤 {message.from_user.full_name}\n💬 {message.text}"
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, feedback_text, parse_mode="HTML")
        except: pass
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("✅ Xabaringiz adminga yuborildi!", reply_markup=get_main_menu(is_admin))

@router.callback_query(F.data == "show_location")
async def show_location(callback: CallbackQuery):
    await callback.message.answer_location(latitude=40.1031, longitude=65.3742)
    await callback.answer("📍 Manzilimiz")
