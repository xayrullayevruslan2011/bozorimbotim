"""
Foydalanuvchi handlerlari
Start, yordam va asosiy menyu
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS, ADMIN_USERNAME
from database import add_user, get_user
from keyboards import get_main_menu, get_contact_keyboard
from states import ContactState

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start komandasi"""
    # Holatni tozalash
    await state.clear()
    
    # Foydalanuvchini bazaga qo'shish
    await add_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name
    )
    
    # Admin ekanligini tekshirish
    is_admin = message.from_user.id in ADMIN_IDS
    
    welcome_text = f"""
🛍 <b>Ruslam|Market</b> ga xush kelibsiz!

Assalomu alaykum, <b>{message.from_user.full_name}</b>! 

Bu yerda siz turli xil mahsulotlarni ko'rishingiz va xarid qilishingiz mumkin.

📱 Quyidagi tugmalardan birini tanlang:
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(is_admin),
        parse_mode="HTML"
    )


@router.message(F.text == "🔙 Orqaga")
async def go_back(message: Message, state: FSMContext):
    """Orqaga qaytish"""
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=get_main_menu(is_admin)
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: Message, state: FSMContext):
    """Amaliyotni bekor qilish"""
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        "❌ Bekor qilindi. Asosiy menyu:",
        reply_markup=get_main_menu(is_admin)
    )


@router.message(F.text == "ℹ️ Ma'lumot")
async def show_info(message: Message):
    """Bot haqida ma'lumot"""
    info_text = """
ℹ️ <b>Ruslam|Market Bot haqida</b>

🛍 Bu bot orqali siz quyidagilarni amalga oshirishingiz mumkin:

✅ Mahsulotlarni ko'rish va tanlash
✅ Savatga qo'shish
✅ Buyurtma berish
✅ Admin bilan bog'lanish

📞 Murojaat uchun: {admin}

🔄 Bot versiyasi: 1.0
👨‍💻 Yaratuvchi: @Ruslanbek20119
""".format(admin=ADMIN_USERNAME)
    
    await message.answer(info_text, parse_mode="HTML")


@router.message(F.text == "⚙️ Sozlamalar")
async def show_settings(message: Message):
    """Sozlamalar"""
    user = await get_user(message.from_user.id)
    
    settings_text = f"""
⚙️ <b>Sozlamalar</b>

👤 <b>Sizning ma'lumotlaringiz:</b>

🆔 ID: <code>{message.from_user.id}</code>
👤 Ism: {message.from_user.full_name}
📧 Username: @{message.from_user.username or "yo'q"}
📅 Ro'yxatdan o'tgan: {user.get('registered_at', "Noma'lum") if user else "Noma'lum"}

Sozlamalarni o'zgartirish uchun admin bilan bog'laning.
"""
    
    await message.answer(settings_text, parse_mode="HTML")


@router.message(F.text == "📞 Biz bilan aloqa")
async def contact_us(message: Message):
    """Biz bilan aloqa"""
    contact_text = f"""
📞 <b>Biz bilan aloqa</b>

Savollaringiz yoki takliflaringiz bo'lsa, biz bilan bog'lanishingiz mumkin:

👨‍💼 Admin: {ADMIN_USERNAME}
📍 Manzil: Navoiy shaxri
🕐 Ish vaqti: 09:00 - 18:00

Quyidagi tugmalardan birini tanlang:
"""
    
    await message.answer(
        contact_text,
        reply_markup=get_contact_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "leave_feedback")
async def leave_feedback(callback: CallbackQuery, state: FSMContext):
    """Xabar qoldirish"""
    await callback.message.edit_text(
        "✍️ <b>Xabaringizni yozing:</b>\n\n"
        "Sizning xabaringiz adminga yuboriladi.",
        parse_mode="HTML"
    )
    await state.set_state(ContactState.message)
    await callback.answer()


@router.message(ContactState.message)
async def process_feedback(message: Message, state: FSMContext):
    """Feedback xabarini qabul qilish"""
    from aiogram import Bot
    from config import ADMIN_IDS
    
    bot: Bot = message.bot
    
    # Adminga xabar yuborish
    feedback_text = f"""
📩 <b>Yangi xabar!</b>

👤 Foydalanuvchi: {message.from_user.full_name}
🆔 ID: <code>{message.from_user.id}</code>
📧 Username: @{message.from_user.username or 'yo\'q'}

💬 <b>Xabar:</b>
{message.text}
"""
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, feedback_text, parse_mode="HTML")
        except:
            pass
    
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    
    await message.answer(
        "✅ Xabaringiz adminga yuborildi! Tez orada javob beramiz.",
        reply_markup=get_main_menu(is_admin)
    )


@router.callback_query(F.data == "show_location")
async def show_location(callback: CallbackQuery):
    """Manzilni ko'rsatish"""
    await callback.message.answer_location(
        latitude=40.1031,
        longitude=65.3742
    )
    await callback.answer("📍 Manzilimiz")
