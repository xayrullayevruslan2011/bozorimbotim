"""
Savat va Buyurtma Handlerlari
- VIP Dizayn (Nusxalash va Chek yuborish)
- Aqlli Qidiruv
- Savatni boshqarish
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

# Database funksiyalari
from database import (
    add_to_cart, get_cart, get_cart_total, update_cart_quantity,
    remove_from_cart, clear_cart, create_order, get_product,
    search_products, add_order
)
# Klaviaturalar
from keyboards import (
    get_cart_keyboard, get_empty_cart_keyboard, get_main_menu,
    get_phone_keyboard, get_confirm_order_keyboard, get_cancel_button,
    get_products_navigation, get_admin_check_keyboard
)
from states import OrderState, SearchState
from config import ADMIN_IDS

router = Router()

# Karta ma'lumotlari
CARD_NUMBER = "4073420067355457"
CARD_OWNER = "Holboyeva Gulzebo"

# =========================================================
# 1. AQLLI QIDIRUV TIZIMI
# =========================================================

@router.message(F.text == "🔍 Qidiruv")
async def cmd_search(message: Message, state: FSMContext):
    """Qidiruvni boshlash"""
    await message.answer(
        "🔎 <b>Qidirayotgan mahsulot nomini yozing:</b>\n"
        "<i>Masalan: Nike, Futbolka...</i>", 
        parse_mode="HTML"
    )
    await state.set_state(SearchState.waiting_for_query)

@router.message(SearchState.waiting_for_query)
async def process_search(message: Message, state: FSMContext):
    """Qidiruv natijalari"""
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("⚠️ Iltimos, kamida 2 ta harf yozing.")
        return

    results = await search_products(query)
    
    if not results:
        await message.answer(f"🤷‍♂️ <b>'{query}'</b> bo'yicha hech narsa topilmadi.", parse_mode="HTML")
        await state.clear()
        return

    await message.answer(f"✅ <b>'{query}'</b> bo'yicha {len(results)} ta mahsulot topildi:")
    
    # Natijani ko'rsatish (products.py dagi funksiyani chaqiramiz)
    from products import show_product_item
    await show_product_item(message, results, 0, results[0]['category_id'])
    await state.clear()


# =========================================================
# 2. SAVATGA QO'SHISH VA KO'RSATISH
# =========================================================

@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_handler(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    await add_to_cart(user_id, product_id)
    product = await get_product(product_id)
    name = product['name'] if product else "Mahsulot"
    await callback.answer(f"✅ {name} savatga qo'shildi!", show_alert=True)

@router.message(F.text == "🛒 Savat")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 <b>Savatingiz bo'sh</b>",
            reply_markup=get_empty_cart_keyboard(),
            parse_mode="HTML"
        )
        return
    
    total = sum(i['price'] * i['quantity'] for i in cart_items)
    text = "🛒 <b>Sizning savatingiz:</b>\n\n"
    for i in cart_items:
        text += f"📦 {i['name']}\n   {i['quantity']} x {i['price']:,} = {i['price']*i['quantity']:,} so'm\n\n"
    text += f"━━━━━━━━━━━━━━━\n💰 <b>Jami: {total:,} so'm</b>"
    
    await message.answer(text, reply_markup=get_cart_keyboard(cart_items), parse_mode="HTML")

# Savatni boshqarish (+, -, o'chirish)
@router.callback_query(F.data.startswith("cart_plus_"))
async def cart_increase(callback: CallbackQuery):
    cart_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    items = await get_cart(user_id)
    for item in items:
        if item['id'] == cart_id:
            await update_cart_quantity(cart_id, item['quantity'] + 1)
            break
    await update_cart_message(callback)

@router.callback_query(F.data.startswith("cart_minus_"))
async def cart_decrease(callback: CallbackQuery):
    cart_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    items = await get_cart(user_id)
    for item in items:
        if item['id'] == cart_id:
            new_qty = item['quantity'] - 1
            if new_qty <= 0: await remove_from_cart(cart_id)
            else: await update_cart_quantity(cart_id, new_qty)
            break
    await update_cart_message(callback)

@router.callback_query(F.data.startswith("cart_remove_"))
async def cart_remove_handler(callback: CallbackQuery):
    await remove_from_cart(int(callback.data.split("_")[2]))
    await update_cart_message(callback)

@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery):
    await clear_cart(callback.from_user.id)
    await callback.message.edit_text("🗑 Savat tozalandi", reply_markup=get_empty_cart_keyboard())

async def update_cart_message(callback: CallbackQuery):
    user_id = callback.from_user.id
    items = await get_cart(user_id)
    if not items:
        await callback.message.edit_text("🛒 Savatingiz bo'sh", reply_markup=get_empty_cart_keyboard())
        return
    total = sum(i['price'] * i['quantity'] for i in items)
    text = "🛒 <b>Sizning savatingiz:</b>\n\n"
    for i in items:
        text += f"📦 {i['name']}\n   {i['quantity']} x {i['price']:,} = {i['price']*i['quantity']:,} so'm\n\n"
    text += f"━━━━━━━━━━━━━━━\n💰 <b>Jami: {total:,} so'm</b>"
    await callback.message.edit_text(text, reply_markup=get_cart_keyboard(items), parse_mode="HTML")


# =========================================================
# 3. BUYURTMA VA VIP TO'LOV DIZAYNI
# =========================================================

@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    if not cart_items:
        await callback.answer("❌ Savat bo'sh!", show_alert=True)
        return
    await callback.message.answer("📱 Telefon raqamingizni yuboring:", reply_markup=get_phone_keyboard())
    await state.set_state(OrderState.phone)
    await callback.message.delete()

@router.message(OrderState.phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    await message.answer("📍 Yetkazib berish manzilini yozing:", reply_markup=get_cancel_button())
    await state.set_state(OrderState.address)

@router.message(OrderState.address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    total = await get_cart_total(message.from_user.id)
    
    # Tasdiqlash tugmalari
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Buyurtmani tasdiqlash", callback_data="confirm_order_final")
    kb.button(text="❌ Bekor qilish", callback_data="cancel_order")
    kb.adjust(1)

    summary = (
        f"📋 <b>Buyurtmani tasdiqlang:</b>\n\n"
        f"📱 Tel: {data['phone']}\n📍 Manzil: {message.text}\n"
        f"💰 Jami: <b>{total:,} so'm</b>"
    )
    await message.answer(summary, reply_markup=kb.as_markup(), parse_mode="HTML")
    await state.set_state(OrderState.confirm)


# 🔥 YANGI: VIP TO'LOV DIZAYNI (RASMDAGIDEK) 🔥
@router.callback_query(OrderState.confirm, F.data == "confirm_order_final")
async def show_vip_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Buyurtma yaratish
    order_id = await create_order(user_id, data['phone'], data['address'])
    
    if not order_id:
        await callback.answer("Xatolik! Qayta urinib ko'ring.", show_alert=True)
        return

    # Tugmalar (Rasmdagidek)
    kb = InlineKeyboardBuilder()
    kb.button(text="♻️ To'lovni tekshirish", callback_data=f"check_pay_{order_id}")
    kb.button(text="💳 Karta raqamni nusxalash", callback_data="copy_card")
    kb.button(text="💰 Summani nusxalash", callback_data="copy_amount")
    kb.button(text="❌ Bekor qilish", callback_data="cancel_order")
    kb.adjust(1)

    text = (
        f"Siz tanladingiz: 📦 <b>Buyurtma #{order_id}</b>\n\n"
        f"💳 <b>TO'LOV QILISH UCHUN</b> 👇\n\n"
        f"👉 PAYME\n👉 CLICK\n👉 PAYNET\n\n"
        f"📌 Iltimos To'lov qilgandan keyin Chekni yuboring\n\n"
        f"💳 <b>Karta orqali:</b>\n<code>{CARD_NUMBER}</code>\n"
        f"👤 <b>{CARD_OWNER}</b>\n\n"
        f"💰 <b>To'lov summasi:</b> To'liq to'lov"
    )
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await state.set_state(OrderState.waiting_for_receipt)
    await state.update_data(current_order_id=order_id)
    
    # Adminga xabar
    await notify_admin(callback.bot, order_id, callback.from_user, data)


# HANDLERLAR: NUSXALASH VA TEKSHIRISH
@router.callback_query(F.data == "copy_card")
async def copy_card_handler(callback: CallbackQuery):
    await callback.message.answer(f"<code>{CARD_NUMBER}</code>", parse_mode="HTML")
    await callback.answer("Nusxalash uchun ustiga bosing 👆")

@router.callback_query(F.data == "copy_amount")
async def copy_amount_handler(callback: CallbackQuery):
    await callback.answer("Summa buyurtma tafsilotlarida ko'rsatilgan", show_alert=True)

@router.callback_query(F.data.startswith("check_pay_"))
async def check_pay_handler(callback: CallbackQuery):
    await callback.message.answer("📸 <b>To'lov chekini rasm qilib yuboring:</b>", parse_mode="HTML")
    await callback.answer()

@router.message(OrderState.waiting_for_receipt, F.photo)
async def receipt_handler(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data.get('current_order_id')
    photo_id = message.photo[-1].file_id
    
    await add_order(message.from_user.id, message.from_user.full_name, photo_id, f"Order #{order_id}", "Tekshirilmoqda")
    
    await message.answer("✅ Chek qabul qilindi! Adminlar tez orada tasdiqlashadi.", reply_markup=get_main_menu())
    
    # Adminga chekni yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                admin_id, photo_id,
                caption=f"🧾 <b>YANGI CHEK!</b>\n🆔 Buyurtma: #{order_id}\n👤 @{message.from_user.username}",
                reply_markup=get_admin_check_keyboard(order_id),
                parse_mode="HTML"
            )
        except: pass
    await state.clear()

@router.callback_query(F.data == "cancel_order")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.message.answer("🏠 Asosiy menyu", reply_markup=get_main_menu())

async def notify_admin(bot, order_id, user, data):
    msg = f"🆕 <b>Yangi buyurtma! #{order_id}</b>\n👤 @{user.username}\n📞 {data['phone']}\n📍 {data['address']}"
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(admin_id, msg, parse_mode="HTML")
        except: pass