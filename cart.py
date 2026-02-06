"""
Savat handlerlari
Savatga qo'shish, o'chirish, buyurtma berish va TO'LOV (Copy function)
Yangi: Aqlli qidiruv tizimi integratsiyasi qo'shildi.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Database funksiyalari (search_products qo'shildi)
from database import (
    add_to_cart,
    get_cart,
    get_cart_total,
    update_cart_quantity,
    remove_from_cart,
    clear_cart,
    create_order,
    get_product,
    search_products 
)
from keyboards import (
    get_cart_keyboard,
    get_empty_cart_keyboard,
    get_main_menu,
    get_phone_keyboard,
    get_confirm_order_keyboard,
    get_cancel_button,
    get_products_navigation # Qidiruv natijalari uchun
)
from states import OrderState, SearchState # SearchState qo'shildi
from config import ADMIN_IDS

router = Router()

# Karta ma'lumotlari
CARD_NUMBER = "4073420067355457"
CARD_OWNER = "Holboyeva Gulzebo"

# =========================================================
# 1. AQLLI QIDIRUV TIZIMI HANDLERLARI (YANGI)
# =========================================================

@router.message(F.text == "🔍 Qidiruv")
async def cmd_search(message: Message, state: FSMContext):
    """Qidiruvni boshlash"""
    await message.answer(
        "🔎 <b>Qidirayotgan mahsulot nomini yozing:</b>\n"
        "<i>Masalan: Oyoq kiyim, Futbolka...</i>", 
        parse_mode="HTML"
    )
    await state.set_state(SearchState.waiting_for_query)

@router.message(SearchState.waiting_for_query)
async def process_search(message: Message, state: FSMContext):
    """Qidiruv natijalarini ko'rsatish"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("⚠️ Iltimos, kamida 2 ta harf yozing.")
        return

    # Bazadan qidirish
    results = await search_products(query)
    
    if not results:
        await message.answer(
            f"🤷‍♂️ Afsuski, <b>'{query}'</b> bo'yicha hech narsa topilmadi.", 
            parse_mode="HTML"
        )
        await state.clear()
        return

    await message.answer(f"✅ <b>'{query}'</b> bo'yicha {len(results)} ta mahsulot topildi:")
    
    # Birinchi natijani ko'rsatish (products.py dagi show_product_item mantiqi kabi)
    from products import show_product_item # Circular import bo'lsa, ichkarida chaqiramiz
    await show_product_item(message, results, 0, results[0]['category_id'])
    await state.clear()


# =========================================================
# 2. SAVATGA QO'SHISH VA KO'RSATISH
# =========================================================

@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_handler(callback: CallbackQuery):
    """Savatga qo'shish (Oddiy usul)"""
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Savatga qo'shish
    await add_to_cart(user_id, product_id)
    
    # Mahsulot nomini olish
    product = await get_product(product_id)
    product_name = product['name'] if product else "Mahsulot"
    
    await callback.answer(f"✅ {product_name} savatga qo'shildi!", show_alert=True)


@router.message(F.text == "🛒 Savat")
async def show_cart(message: Message):
    """Savatni ko'rsatish"""
    user_id = message.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 <b>Savatingiz bo'sh</b>\n\n"
            "Mahsulotlarni ko'rish uchun quyidagi tugmani bosing:",
            reply_markup=get_empty_cart_keyboard(),
            parse_mode="HTML"
        )
        return
    
    cart_text = "🛒 <b>Sizning savatingiz:</b>\n\n"
    total = 0
    for item in cart_items:
        item_total = item['price'] * item['quantity']
        total += item_total
        cart_text += f"📦 {item['name']}\n"
        cart_text += f"   {item['quantity']} x {item['price']:,} = {item_total:,} so'm\n\n"
    
    cart_text += f"━━━━━━━━━━━━━━━\n"
    cart_text += f"💰 <b>Jami: {total:,} so'm</b>"
    
    await message.answer(
        cart_text,
        reply_markup=get_cart_keyboard(cart_items),
        parse_mode="HTML"
    )

# ... (Savat amallari: cart_plus, cart_minus, cart_remove, clear_cart, update_cart_message o'zgarishsiz qoladi)

@router.callback_query(F.data.startswith("cart_plus_"))
async def cart_increase(callback: CallbackQuery):
    cart_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    for item in cart_items:
        if item['id'] == cart_id:
            await update_cart_quantity(cart_id, item['quantity'] + 1)
            break
    await update_cart_message(callback)

@router.callback_query(F.data.startswith("cart_minus_"))
async def cart_decrease(callback: CallbackQuery):
    cart_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    for item in cart_items:
        if item['id'] == cart_id:
            new_quantity = item['quantity'] - 1
            if new_quantity <= 0:
                await remove_from_cart(cart_id)
            else:
                await update_cart_quantity(cart_id, new_quantity)
            break
    await update_cart_message(callback)

@router.callback_query(F.data.startswith("cart_remove_"))
async def cart_remove_handler(callback: CallbackQuery):
    cart_id = int(callback.data.split("_")[2])
    await remove_from_cart(cart_id)
    await callback.answer("🗑 O'chirildi")
    await update_cart_message(callback)

@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery):
    await clear_cart(callback.from_user.id)
    await callback.message.edit_text(
        "🗑 <b>Savat tozalandi</b>\n\n"
        "Mahsulotlarni ko'rish uchun quyidagi tugmani bosing:",
        reply_markup=get_empty_cart_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("🗑 Savat tozalandi")

async def update_cart_message(callback: CallbackQuery):
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    if not cart_items:
        await callback.message.edit_text(
            "🛒 <b>Savatingiz bo'sh</b>",
            reply_markup=get_empty_cart_keyboard(),
            parse_mode="HTML"
        )
        return
    cart_text = "🛒 <b>Sizning savatingiz:</b>\n\n"
    total = sum(i['price'] * i['quantity'] for i in cart_items)
    for i in cart_items:
        cart_text += f"📦 {i['name']}\n   {i['quantity']} x {i['price']:,} = {i['price']*i['quantity']:,} so'm\n\n"
    cart_text += f"━━━━━━━━━━━━━━━\n💰 <b>Jami: {total:,} so'm</b>"
    await callback.message.edit_text(cart_text, reply_markup=get_cart_keyboard(cart_items), parse_mode="HTML")
    await callback.answer()

# ============ BUYURTMA BERISH (CHECKOUT) ============

@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    if not cart_items:
        await callback.answer("❌ Savat bo'sh!", show_alert=True)
        return
    await callback.message.edit_text(
        "📱 <b>Bog'lanish uchun telefon raqamingizni yuboring:</b>\n\n"
        "Pastdagi tugmani bosing 👇 yoki qo'lda yozing (+998...)",
        parse_mode="HTML"
    )
    await callback.message.answer("📱 Telefon raqamni yuborish:", reply_markup=get_phone_keyboard())
    await state.set_state(OrderState.phone)
    await callback.answer()

@router.message(OrderState.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await ask_address(message, state)

@router.message(OrderState.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    if not any(char.isdigit() for char in message.text):
        await message.answer("❌ Iltimos, to'g'ri telefon raqam kiriting!")
        return
    await state.update_data(phone=message.text)
    await ask_address(message, state)

async def ask_address(message: Message, state: FSMContext):
    await message.answer(
        "📍 <b>Yetkazib berish manzilini yozing:</b>",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(OrderState.address)

@router.message(OrderState.address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    cart_items = await get_cart(message.from_user.id)
    total = sum(i['price'] * i['quantity'] for i in cart_items)
    order_text = "📋 <b>Buyurtmani tasdiqlang:</b>\n\n"
    for item in cart_items:
        order_text += f"📦 {item['name']} x {item['quantity']} = {item['price']*item['quantity']:,} so'm\n"
    order_text += f"\n━━━━━━━━━━━━━━━\n💰 <b>Jami: {total:,} so'm</b>\n\n"
    order_text += f"📱 Telefon: {data['phone']}\n📍 Manzil: {message.text}"
    await message.answer(order_text, reply_markup=get_confirm_order_keyboard(), parse_mode="HTML")
    await state.set_state(OrderState.confirm)

@router.callback_query(OrderState.confirm, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = await create_order(callback.from_user.id, data['phone'], data['address'])
    if order_id:
        await notify_admin_new_order(callback.bot, order_id, callback.from_user, data)
        await callback.message.edit_text(
            f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n🆔 Buyurtma: <code>#{order_id}</code>\n\n"
            f"💳 <b>TO'LOV KARTASI:</b>\n<code>{CARD_NUMBER}</code>\n👤 <b>{CARD_OWNER}</b>\n\n"
            f"📝 To'lov chekini @Ruslanbek20119 ga yuboring.",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Xatolik yuz berdi.")
    await state.clear()
    await callback.message.answer("🏠 Asosiy menyu:", reply_markup=get_main_menu(callback.from_user.id in ADMIN_IDS))
    await callback.answer()

@router.callback_query(OrderState.confirm, F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.")
    await callback.message.answer("🏠 Asosiy menyu:", reply_markup=get_main_menu(callback.from_user.id in ADMIN_IDS))
    await callback.answer()

async def notify_admin_new_order(bot: Bot, order_id: int, user, data: dict):
    text = f"🆕 <b>Yangi buyurtma!</b>\n🆔 Buyurtma raqami: #{order_id}\n\n👤 Mijoz: @{user.username or 'mavjud_emas'}\n📞 Telefon: {data.get('phone')}\n📍 Manzil: {data.get('address')}"
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(admin_id, text, parse_mode="HTML")
        except: pass