"""
Foydalanuvchi handlerlari
Start, yordam, asosiy menyu + MAJBURIY OBUNA + LIMIT + TO'LOV TIZIMI + ONLINE KURSLAR (YANGI)
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

# Kerakli narsalarni import qilamiz
from config import ADMIN_IDS, ADMIN_USERNAME, REQUIRED_CHANNELS 
from database import add_user, get_user # Eski baza (userlar uchun)
import db # 🆕 YANGI baza (buyurtmalar uchun)

# 🆕 TUGMALARNI IMPORT QILAMIZ
from keyboards import (
    get_main_menu, 
    get_contact_keyboard, 
    get_subscription_keyboard, 
    get_limit_keyboard,
    get_payment_cancel_keyboard,    # 🆕
    get_user_orders_navigation,     # 🆕
    get_admin_check_keyboard,       # 🆕
    # YANGI QO'SHILGANLAR:
    get_tariffs_keyboard,           
    get_payment_actions_keyboard
)
from states import ContactState, CheckoutState 

router = Router()

# Karta ma'lumotlari (Kurslar uchun)
CARD_NUMBER = "4073420067355457"
CARD_OWNER = "Holboyeva Gulzebo"

# ==================================================
# 1. A'ZOLIKNI TEKSHIRISH
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
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """Start komandasi"""
    await state.clear()
    
    # Foydalanuvchini bazaga qo'shish
    await add_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name
    )
    
    # --- OBUNANI TEKSHIRISH ---
    is_subscribed = await check_sub_status(bot, message.from_user.id)
    
    if not is_subscribed:
        await message.answer(
            f"👋 <b>Assalomu alaykum, {message.from_user.full_name}!</b>\n\n"
            "Botdan to'liq foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_subscription_keyboard(),
            parse_mode="HTML"
        )
        return # Kod shu yerda to'xtaydi

    # --- AGAR A'ZO BO'LSA ---
    is_admin = message.from_user.id in ADMIN_IDS
    
    welcome_text = f"""
🛍 <b>Ruslan|Market</b> ga xush kelibsiz!

Assalomu alaykum, <b>{message.from_user.full_name}</b>! 

Bu yerda siz turli xil mahsulotlarni ko'rishingiz va xarid qilishingiz mumkin.

📱 Quyidagi tugmalardan birini tanlang:
"""
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(is_admin),
        parse_mode="HTML"
    )

# ==================================================
# 3. OBUNANI TEKSHIRISH TUGMASI UCHUN
# ==================================================
@router.callback_query(F.data == "check_subscription")
async def check_btn(callback: CallbackQuery, bot: Bot):
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
        await callback.answer("❌ Hali to'liq a'zo bo'lmadingiz!", show_alert=True)


# ==================================================
# 🔥 LIMIT OLISH HANLDERI 🔥
# ==================================================
@router.message(F.text == "💰 Limit olish")
async def limit_handler(message: Message):
    text = (
        "<b>🚀 Nasiya Limitini Tekshirish</b>\n\n"
        "Marhamat, pastdagi tugmani bosib, o'z limitingizni tekshirib oling! 👇"
    )
    await message.answer(text, reply_markup=get_limit_keyboard())


# ==================================================
# 🔥 TO'LOV VA CHEK YUBORISH TIZIMI (UMUMIY) 🔥
# ==================================================

# 1. "Buyurtmani rasmiylashtirish" (Savatdan)
@router.callback_query(F.data == "checkout")
async def start_checkout_process(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    text = (
        f"💳 <b>To'lov uchun karta:</b>\n"
        f"<code>{CARD_NUMBER}</code> ({CARD_OWNER})\n\n"
        "Iltimos, to'lovni amalga oshiring va <b>chek rasmini</b> shu yerga yuboring:" 
    )
    # Bekor qilish tugmasi bilan chiqarish
    await call.message.answer(text, parse_mode="HTML", reply_markup=get_payment_cancel_keyboard())
    
    # Botni "Rasm kutish" rejimiga o'tkazamiz va mahsulot nomini saqlab qo'yamiz
    await state.update_data(product_name="Savatdagi mahsulotlar")
    await state.set_state(CheckoutState.waiting_for_receipt)

# 2. To'lov paytida "Bekor qilish" bosilsa
@router.message(CheckoutState.waiting_for_receipt, F.text == "❌ To'lovni bekor qilish")
async def cancel_checkout(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("❌ To'lov bekor qilindi.", reply_markup=get_main_menu(is_admin))

# 3. Foydalanuvchi CHEK (Rasm) yuborganda
@router.message(CheckoutState.waiting_for_receipt, F.photo)
async def process_receipt(message: Message, state: FSMContext, bot: Bot):
    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    # State dan ma'lumotni olamiz (qaysi mahsulot yoki tarif uchun to'lov qilingan)
    data = await state.get_data()
    product_name = data.get("product_name", "Noma'lum to'lov")

    # Bazaga yozamiz
    order_id = db.db.add_order(user_id, full_name, photo_id, product_name, "Hisoblanmoqda...")
    
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
    
    # Barcha adminlarga yuborish
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


# ==================================================
# 🔥 MENING BUYURTMALARIM 🔥
# ==================================================
@router.message(F.text == "📦 Mening buyurtmalarim")
async def show_my_orders(message: Message):
    # Bazadan shu odamning buyurtmalarini olamiz
    orders = db.db.get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("🤷‍♂️ Sizda hali buyurtmalar yo'q.")
        return

    # Birinchi (eng oxirgi) buyurtmani ko'rsatamiz
    current_index = 0
    total_orders = len(orders)
    order = orders[current_index]
    
    # order strukturasi: (id, user_id, full_name, photo_id, products, total_price, track_code, status)
    # Eslatma: products bu yerda tarif nomi bo'lishi ham mumkin
    msg = (
        f"📦 <b>Buyurtma #{order[0]}</b>\n"
        f"🛍 Mahsulot: {order[4]}\n"
        f"ℹ️ Holat: {order[7]}\n\n"
        f"🔢 <b>Trek raqam:</b> <code>{order[6]}</code>"
    )
    
    await message.answer_photo(
        photo=order[3], # Chek rasmi
        caption=msg,
        parse_mode="HTML",
        reply_markup=get_user_orders_navigation(current_index, total_orders)
    )

# Buyurtmalarni varaqlash (Oldingi / Keyingi)
@router.callback_query(F.data.startswith("my_orders_"))
async def navigate_orders(callback: CallbackQuery):
    action = callback.data.split("_")[2] # prev yoki next
    current_index = int(callback.data.split("_")[3])
    
    orders = db.db.get_user_orders(callback.from_user.id)
    total_orders = len(orders)

    # Indeksni hisoblash
    if action == "prev":
        new_index = max(0, current_index - 1)
    elif action == "next":
        new_index = min(total_orders - 1, current_index + 1)
    else:
        new_index = current_index

    # Agar indeks o'zgarmasa, hech narsa qilmaymiz
    if new_index == current_index:
        await callback.answer()
        return

    order = orders[new_index]
    msg = (
        f"📦 <b>Buyurtma #{order[0]}</b>\n"
        f"🛍 Mahsulot: {order[4]}\n"
        f"ℹ️ Holat: {order[7]}\n\n"
        f"🔢 <b>Trek raqam:</b> <code>{order[6]}</code>"
    )
    
    from aiogram.types import InputMediaPhoto
    media = InputMediaPhoto(media=order[3], caption=msg, parse_mode="HTML")
    
    await callback.message.edit_media(
        media=media,
        reply_markup=get_user_orders_navigation(new_index, total_orders)
    )

@router.callback_query(F.data == "close_my_orders")
async def close_orders_window(callback: CallbackQuery):
    await callback.message.delete()


# ==================================================
# 🔥 ONLINE KURSLAR (YANGI TARIFLAR TIZIMI) 🔥
# ==================================================

# 1. "🎓 Online Kurslar" tugmasi bosilganda
@router.message(F.text == "🎓 Online Kurslar")
async def show_courses_handler(message: Message):
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


# 2. Tarif tanlanganda (Start, Pro, VIP) -> To'lov ma'lumotlari chiqadi
@router.callback_query(F.data.startswith("tariff_"))
async def select_tariff_handler(call: CallbackQuery, state: FSMContext):
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

    # State ga qaysi tarifni tanlaganini yozib qo'yamiz (keyin chek yuborganda kerak bo'ladi)
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

    # Eski xabarni o'chirib, yangisini yuboramiz
    await call.message.delete()
    await call.message.answer(text, parse_mode="HTML", reply_markup=get_payment_actions_keyboard(price))


# 3. "Karta raqamni nusxalash" bosilganda
@router.callback_query(F.data == "copy_card_number")
async def copy_card_handler(call: CallbackQuery):
    await call.message.answer(f"<code>{CARD_NUMBER}</code>", parse_mode="HTML")
    await call.answer("Karta raqami yuborildi! Nusxalash uchun ustiga bosing.", show_alert=True)


# 4. "Summani nusxalash" bosilganda
@router.callback_query(F.data.startswith("copy_amount_"))
async def copy_amount_handler(call: CallbackQuery):
    amount = call.data.split("_")[2] # "100 000" ni ajratib oladi
    clean_amount = amount.replace(" ", "")
    
    await call.message.answer(f"<code>{clean_amount}</code>", parse_mode="HTML")
    await call.answer(f"Summa ({clean_amount}) nusxalash uchun yuborildi!", show_alert=True)


# 5. "Tekshirish" bosilganda -> Rasm so'raymiz
@router.callback_query(F.data == "check_payment")
async def check_payment_handler(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    # Rasm kutish rejimiga o'tamiz
    await state.set_state(CheckoutState.waiting_for_receipt)
    
    await call.message.answer(
        "📸 <b>Iltimos, to'lov chekini rasm qilib yuboring.</b>",
        reply_markup=get_payment_cancel_keyboard(), # Bekor qilish tugmasi chiqadi
        parse_mode="HTML"
    )
    await call.answer()


# 6. "Yopish" tugmasi
@router.callback_query(F.data == "delete_message")
async def delete_msg_handler(call: CallbackQuery):
    await call.message.delete()


# ==================================================
# QOLGAN HANDLERLAR
# ==================================================

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
🔄 Bot versiyasi: 1.0
👨‍💻 Yaratuvchi: @Ruslanbek20119
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
    # ==================================================
# 🔥 YANGI: ONLINE KURSLAR (SAYTSIZ - TELEGRAM ICHIDA) 🔥
# ==================================================

# 1. "🎓 Online Kurslar" tugmasi bosilganda -> Tariflar chiqadi
@router.message(F.text == "🎓 Online Kurslar")
async def show_courses_handler(message: Message):
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
    # Sayt linki YO'Q, o'rniga Tarif tugmalari chiqadi
    await message.answer(text, reply_markup=get_tariffs_keyboard())


# 2. Tarif tanlanganda (Start, Pro, VIP) -> To'lov ma'lumotlari chiqadi
@router.callback_query(F.data.startswith("tariff_"))
async def select_tariff_handler(call: CallbackQuery, state: FSMContext):
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

    # State ga qaysi tarifni tanlaganini yozib qo'yamiz
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
    # To'lov tugmalari (Nusxalash, Tekshirish)
    await call.message.answer(text, parse_mode="HTML", reply_markup=get_payment_actions_keyboard(price))