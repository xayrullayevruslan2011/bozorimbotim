"""
Savat handlerlari
Savatga qo'shish, o'chirish, buyurtma berish
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import (
    add_to_cart,
    get_cart,
    get_cart_total,
    update_cart_quantity,
    remove_from_cart,
    clear_cart,
    create_order,
    get_product
)
from keyboards import (
    get_cart_keyboard,
    get_empty_cart_keyboard,
    get_main_menu,
    get_phone_keyboard,
    get_confirm_order_keyboard,
    get_cancel_button
)
from states import OrderState
from config import ADMIN_IDS

router = Router()


@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_handler(callback: CallbackQuery):
    """Savatga qo'shish"""
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
    
    # Savat tarkibini ko'rsatish
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


@router.callback_query(F.data.startswith("cart_plus_"))
async def cart_increase(callback: CallbackQuery):
    """Miqdorni oshirish"""
    cart_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    cart_items = await get_cart(user_id)
    for item in cart_items:
        if item['id'] == cart_id:
            await update_cart_quantity(cart_id, item['quantity'] + 1)
            break
    
    # Savatni qayta ko'rsatish
    await update_cart_message(callback)


@router.callback_query(F.data.startswith("cart_minus_"))
async def cart_decrease(callback: CallbackQuery):
    """Miqdorni kamaytirish"""
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
    
    # Savatni qayta ko'rsatish
    await update_cart_message(callback)


@router.callback_query(F.data.startswith("cart_remove_"))
async def cart_remove(callback: CallbackQuery):
    """Savatdan o'chirish"""
    cart_id = int(callback.data.split("_")[2])
    
    await remove_from_cart(cart_id)
    await callback.answer("🗑 O'chirildi")
    
    # Savatni qayta ko'rsatish
    await update_cart_message(callback)


@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery):
    """Savatni tozalash"""
    await clear_cart(callback.from_user.id)
    
    await callback.message.edit_text(
        "🗑 <b>Savat tozalandi</b>\n\n"
        "Mahsulotlarni ko'rish uchun quyidagi tugmani bosing:",
        reply_markup=get_empty_cart_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("🗑 Savat tozalandi")


async def update_cart_message(callback: CallbackQuery):
    """Savat xabarini yangilash"""
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
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
    
    await callback.message.edit_text(
        cart_text,
        reply_markup=get_cart_keyboard(cart_items),
        parse_mode="HTML"
    )
    await callback.answer()


# ============ BUYURTMA BERISH ============

@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    """Buyurtmani rasmiylashtirish"""
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await callback.answer("❌ Savat bo'sh!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📱 <b>Telefon raqamingizni yuboring:</b>\n\n"
        "Quyidagi tugmani bosing yoki qo'lda kiriting:",
        parse_mode="HTML"
    )
    
    await callback.message.answer(
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=get_phone_keyboard()
    )
    
    await state.set_state(OrderState.phone)
    await callback.answer()


@router.message(OrderState.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Telefon raqamni kontaktdan olish"""
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    
    await message.answer(
        "📍 <b>Yetkazib berish manzilini kiriting:</b>\n\n"
        "Masalan: Toshkent sh., Chilonzor tumani, 1-kvartal, 5-uy",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(OrderState.address)


@router.message(OrderState.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    """Telefon raqamni matndan olish"""
    phone = message.text
    
    # Telefon raqamni tekshirish
    if not phone.replace("+", "").replace(" ", "").isdigit():
        await message.answer(
            "❌ Noto'g'ri format! Iltimos, telefon raqamingizni kiriting:",
            reply_markup=get_phone_keyboard()
        )
        return
    
    await state.update_data(phone=phone)
    
    await message.answer(
        "📍 <b>Yetkazib berish manzilini kiriting:</b>\n\n"
        "Masalan: Toshkent sh., Chilonzor tumani, 1-kvartal, 5-uy",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(OrderState.address)


@router.message(OrderState.address)
async def process_address(message: Message, state: FSMContext):
    """Manzilni qabul qilish"""
    address = message.text
    await state.update_data(address=address)
    
    # Buyurtma ma'lumotlarini ko'rsatish
    data = await state.get_data()
    user_id = message.from_user.id
    
    cart_items = await get_cart(user_id)
    total = await get_cart_total(user_id)
    
    order_text = "📋 <b>Buyurtmangizni tasdiqlang:</b>\n\n"
    
    for item in cart_items:
        item_total = item['price'] * item['quantity']
        order_text += f"📦 {item['name']} x {item['quantity']} = {item_total:,} so'm\n"
    
    order_text += f"\n━━━━━━━━━━━━━━━\n"
    order_text += f"💰 <b>Jami: {total:,} so'm</b>\n\n"
    order_text += f"📱 Telefon: {data['phone']}\n"
    order_text += f"📍 Manzil: {address}"
    
    await message.answer(
        order_text,
        reply_markup=get_confirm_order_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderState.confirm)


@router.callback_query(OrderState.confirm, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Buyurtmani tasdiqlash"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Buyurtma yaratish
    order_id = await create_order(
        user_id=user_id,
        phone=data['phone'],
        address=data['address']
    )
    
    if order_id:
        # Adminga xabar yuborish
        await notify_admin_new_order(callback.bot, order_id, callback.from_user, data)
        
        await callback.message.edit_text(
            f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
            f"🆔 Buyurtma raqami: <code>#{order_id}</code>\n\n"
            f"Tez orada siz bilan bog'lanamiz! 📞",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring."
        )
    
    await state.clear()
    is_admin = callback.from_user.id in ADMIN_IDS
    await callback.message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=get_main_menu(is_admin)
    )
    await callback.answer()


@router.callback_query(OrderState.confirm, F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Buyurtmani bekor qilish"""
    await state.clear()
    is_admin = callback.from_user.id in ADMIN_IDS
    
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.")
    await callback.message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=get_main_menu(is_admin)
    )
    await callback.answer()


async def notify_admin_new_order(bot: Bot, order_id: int, user, data: dict):
    """Adminga yangi buyurtma haqida xabar yuborish"""
    from database import get_order_items, get_order
    
    order = await get_order(order_id)
    items = await get_order_items(order_id)
    
    admin_text = f"""
🆕 <b>Yangi buyurtma!</b>

🆔 Buyurtma: <code>#{order_id}</code>

👤 Mijoz: {user.full_name}
📧 Username: @{user.username or 'yo\'q'}
📱 Telefon: {data['phone']}
📍 Manzil: {data['address']}

📦 <b>Mahsulotlar:</b>
"""
    
    for item in items:
        admin_text += f"  • {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n"
    
    admin_text += f"\n💰 <b>Jami: {order['total_amount']:,} so'm</b>"
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="HTML")
        except:
            pass
