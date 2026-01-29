"""
Admin handlerlari
Mahsulot qo'shish/o'chirish, statistika, xabar yuborish + BUYURTMALAR + FIREBASE (KURSLAR)
"""
import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# 🔥 FIREBASE KUTUBXONALARI (YANGI)
import firebase_admin
from firebase_admin import credentials, firestore

from config import ADMIN_IDS
# Eski baza importlari (Mahsulotlar uchun)
from database import (
    get_categories,
    add_category,
    delete_category,
    get_all_products,
    add_product,
    delete_product,
    get_all_users,
    get_users_count,
    get_orders_count
)
# 🆕 Yangi baza importi (Buyurtmalar va Trek kod uchun)
import db 

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

# ==================================================
# 🔥 FIREBASE NI ISHGA TUSHIRISH (KURSLAR UCHUN)
# ==================================================
if not firebase_admin._apps:
    try:
        # Fayl nomi aniq firebase_key.json bo'lishi kerak!
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase muvaffaqiyatli ulandi!")
    except Exception as e:
        print(f"❌ Firebase xatosi: {e}")
        print("⚠️ Iltimos, firebase_key.json fayli borligini tekshiring!")

# Bazani olish
db_firebase = firestore.client()


# ============ ADMIN TEKSHIRUVI ============

def is_admin(user_id: int) -> bool:
    """Admin ekanligini tekshirish"""
    return user_id in ADMIN_IDS


@router.message(F.text == "👨‍💼 Admin Panel")
async def admin_panel(message: Message):
    """Admin panel"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin huquqlari yo'q!")
        return
    
    await message.answer(
        "👨‍💼 <b>Admin Panel</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="HTML"
    )


# ============ STATISTIKA ============

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Statistika"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    
    users_count = await get_users_count()
    orders_count = await get_orders_count()
    products = await get_all_products()
    categories = await get_categories()
    
    stats_text = f"""
📊 <b>Statistika</b>

👥 Foydalanuvchilar: {users_count}
📦 Buyurtmalar: {orders_count}
🛍 Mahsulotlar: {len(products)}
📁 Kategoriyalar: {len(categories)}
"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ============ KATEGORIYALAR BOSHQARUVI ============

@router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: CallbackQuery):
    """Kategoriyalar boshqaruvi"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    
    categories = await get_categories()
    
    await callback.message.edit_text(
        "📁 <b>Kategoriyalar boshqaruvi</b>\n\n"
        "Kategoriyani tanlang yoki yangi qo'shing:",
        reply_markup=get_admin_categories_keyboard(categories),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "add_category")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    """Kategoriya qo'shishni boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📁 <b>Yangi kategoriya qo'shish</b>\n\n"
        "Kategoriya nomini kiriting:"
    )
    await callback.message.answer(
        "Kategoriya nomini kiriting:",
        reply_markup=get_cancel_button()
    )
    await state.set_state(AddCategoryState.name)
    await callback.answer()


@router.message(AddCategoryState.name)
async def process_category_name(message: Message, state: FSMContext):
    """Kategoriya nomi"""
    await state.update_data(name=message.text)
    
    await message.answer(
        "Kategoriya uchun emoji kiriting (masalan: 📦):",
        reply_markup=get_skip_button()
    )
    await state.set_state(AddCategoryState.emoji)


@router.message(AddCategoryState.emoji)
async def process_category_emoji(message: Message, state: FSMContext):
    """Kategoriya emojisi"""
    if message.text == "⏭ O'tkazib yuborish":
        emoji = "📦"
    else:
        emoji = message.text
    
    data = await state.get_data()
    
    # Kategoriya qo'shish
    await add_category(data['name'], emoji)
    
    await state.clear()
    await message.answer(
        f"✅ Kategoriya qo'shildi: {emoji} {data['name']}",
        reply_markup=get_main_menu(True)
    )


@router.callback_query(F.data.startswith("delete_cat_"))
async def delete_category_handler(callback: CallbackQuery):
    """Kategoriyani o'chirish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[2])
    await delete_category(category_id)
    
    # Ro'yxatni yangilash
    categories = await get_categories()
    await callback.message.edit_text(
        "📁 <b>Kategoriyalar boshqaruvi</b>\n\n"
        "Kategoriyani tanlang yoki yangi qo'shing:",
        reply_markup=get_admin_categories_keyboard(categories),
        parse_mode="HTML"
    )
    await callback.answer("🗑 O'chirildi")


# ============ MAHSULOTLAR BOSHQARUVI ============

@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    """Mahsulotlar boshqaruvi"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    
    products = await get_all_products()
    
    await callback.message.edit_text(
        "📦 <b>Mahsulotlar boshqaruvi</b>\n\n"
        f"Jami: {len(products)} ta mahsulot",
        reply_markup=get_admin_products_keyboard(products),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    """Mahsulot qo'shishni boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    
    categories = await get_categories()
    
    if not categories:
        await callback.answer("❌ Avval kategoriya qo'shing!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📦 <b>Yangi mahsulot qo'shish</b>\n\n"
        "Kategoriyani tanlang:",
        reply_markup=get_admin_select_category_keyboard(categories),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.category)
    await callback.answer()


@router.callback_query(AddProductState.category, F.data.startswith("select_cat_"))
async def select_product_category(callback: CallbackQuery, state: FSMContext):
    """Mahsulot uchun kategoriya tanlash"""
    category_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=category_id)
    
    await callback.message.edit_text(
        "📝 <b>Mahsulot nomini kiriting:</b>",
        parse_mode="HTML"
    )
    await callback.message.answer(
        "Mahsulot nomini kiriting:",
        reply_markup=get_cancel_button()
    )
    await state.set_state(AddProductState.name)
    await callback.answer()


@router.callback_query(AddProductState.category, F.data == "cancel_add_product")
async def cancel_add_product(callback: CallbackQuery, state: FSMContext):
    """Mahsulot qo'shishni bekor qilish"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Bekor qilindi.",
    )
    await callback.message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=get_main_menu(True)
    )
    await callback.answer()


@router.message(AddProductState.name)
async def process_product_name(message: Message, state: FSMContext):
    """Mahsulot nomi"""
    await state.update_data(name=message.text)
    
    await message.answer(
        "📝 <b>Mahsulot tavsifini kiriting:</b>",
        reply_markup=get_skip_button(),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.description)


@router.message(AddProductState.description)
async def process_product_description(message: Message, state: FSMContext):
    """Mahsulot tavsifi"""
    if message.text == "⏭ O'tkazib yuborish":
        description = ""
    else:
        description = message.text
    
    await state.update_data(description=description)
    
    await message.answer(
        "💰 <b>Mahsulot narxini kiriting (so'mda):</b>",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.price)


@router.message(AddProductState.price)
async def process_product_price(message: Message, state: FSMContext):
    """Mahsulot narxi"""
    try:
        price = int(message.text.replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting:")
        return
    
    await state.update_data(price=price)
    
    await message.answer(
        "🖼 <b>Mahsulot rasmini yuboring:</b>",
        reply_markup=get_skip_button(),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.photo)


@router.message(AddProductState.photo, F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    """Mahsulot rasmi"""
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    
    await message.answer(
        "📊 <b>Ombordagi sonini kiriting:</b>",
        reply_markup=get_skip_button(),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.stock)


@router.message(AddProductState.photo, F.text == "⏭ O'tkazib yuborish")
async def skip_product_photo(message: Message, state: FSMContext):
    """Rasmni o'tkazib yuborish"""
    await state.update_data(photo_id=None)
    
    await message.answer(
        "📊 <b>Ombordagi sonini kiriting:</b>",
        reply_markup=get_skip_button(),
        parse_mode="HTML"
    )
    await state.set_state(AddProductState.stock)


@router.message(AddProductState.stock)
async def process_product_stock(message: Message, state: FSMContext):
    """Mahsulot soni"""
    if message.text == "⏭ O'tkazib yuborish":
        stock = 0
    else:
        try:
            stock = int(message.text)
        except ValueError:
            await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting:")
            return
    
    # Barcha ma'lumotlarni olish
    data = await state.get_data()
    
    # Mahsulot qo'shish
    product_id = await add_product(
        category_id=data['category_id'],
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        photo_id=data.get('photo_id'),
        stock=stock
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Mahsulot qo'shildi!</b>\n\n"
        f"📦 {data['name']}\n"
        f"💰 {data['price']:,} so'm\n"
        f"📊 Omborda: {stock} dona",
        reply_markup=get_main_menu(True),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("delete_prod_"))
async def delete_product_handler(callback: CallbackQuery):
    """Mahsulotni o'chirish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[2])
    await delete_product(product_id)
    
    # Ro'yxatni yangilash
    products = await get_all_products()
    await callback.message.edit_text(
        "📦 <b>Mahsulotlar boshqaruvi</b>\n\n"
        f"Jami: {len(products)} ta mahsulot",
        reply_markup=get_admin_products_keyboard(products),
        parse_mode="HTML"
    )
    await callback.answer("🗑 O'chirildi")


# ============ XABAR YUBORISH (BROADCAST) ============

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    """Xabar yuborish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>Xabar yuborish</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:",
        parse_mode="HTML"
    )
    await callback.message.answer(
        "Xabar matnini kiriting:",
        reply_markup=get_cancel_button()
    )
    await state.set_state(BroadcastState.message)
    await callback.answer()


@router.message(BroadcastState.message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Xabar matnini qabul qilish"""
    await state.update_data(message=message.text, message_id=message.message_id)
    
    users_count = await get_users_count()
    
    await message.answer(
        f"📢 <b>Xabarni tasdiqlang</b>\n\n"
        f"👥 Qabul qiluvchilar: {users_count} ta foydalanuvchi\n\n"
        f"📝 <b>Xabar:</b>\n{message.text}",
        reply_markup=get_broadcast_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(BroadcastState.confirm)


@router.callback_query(BroadcastState.confirm, F.data == "confirm_broadcast")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Xabar yuborishni tasdiqlash"""
    data = await state.get_data()
    message_text = data['message']
    
    users = await get_all_users()
    
    success = 0
    failed = 0
    
    await callback.message.edit_text("⏳ Xabarlar yuborilmoqda...")
    
    for user_id in users:
        try:
            await callback.bot.send_message(
                user_id,
                f"📢 <b>Yangilik!</b>\n\n{message_text}",
                parse_mode="HTML"
            )
            success += 1
        except:
            failed += 1
    
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Muvaffaqiyatsiz: {failed}",
        parse_mode="HTML"
    )
    await callback.message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=get_main_menu(True)
    )


@router.callback_query(BroadcastState.confirm, F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Xabar yuborishni bekor qilish"""
    await state.clear()
    
    await callback.message.edit_text("❌ Xabar yuborish bekor qilindi.")
    await callback.message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=get_main_menu(True)
    )
    await callback.answer()


# ==================================================
# 🔥 BUYURTMALAR BOSHQARUVI (MAHSULOTLAR UCHUN) 🔥
# ==================================================

@router.callback_query(F.data == "admin_orders")
async def admin_orders_list(callback: CallbackQuery):
    """Oxirgi buyurtmalarni ko'rish tugmasi bosilganda"""
    orders_count = await get_orders_count()
    await callback.answer(f"Jami buyurtmalar: {orders_count} ta.\nYangi buyurtmalar sizga rasm shaklida keladi.", show_alert=True)


# 1. Admin "TASDIQLASH" tugmasini bossa (Buyurtma chek tagida)
@router.callback_query(F.data.startswith("admin_confirm_"))
async def approve_order_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

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


# 2. Admin Trek kodni yozganda
@router.message(AdminState.waiting_for_track)
async def process_track_code(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Trek kodi kiritish bekor qilindi.", reply_markup=get_main_menu(True))
        return

    track_code = message.text
    data = await state.get_data()
    order_id = data.get('order_id')
    
    # 1. Bazani yangilash
    db.db.update_track_code(order_id, track_code)
    
    # 2. Buyurtma egasini topish
    order = db.db.get_order(order_id)
    if order:
        user_id = order[1] # user_id 2-ustunda
        
        # 3. Mijozga xabar yuborish
        try:
            await bot.send_message(
                user_id,
                f"✅ <b>Sizning #{order_id} buyurtmangiz tasdiqlandi!</b>\n\n"
                f"🔢 <b>Trek kodingiz:</b> <code>{track_code}</code>\n\n"
                f"Uni 📦 'Mening buyurtmalarim' bo'limida ham ko'rishingiz mumkin.",
                parse_mode="HTML"
            )
            await message.answer(f"✅ Trek kod saqlandi va mijozga yuborildi:\n<code>{track_code}</code>", reply_markup=get_main_menu(True), parse_mode="HTML")
        except Exception as e:
            await message.answer(f"⚠️ Trek saqlandi, lekin mijozga xabar bora olmadi (Bloklagan bo'lishi mumkin).\nXato: {e}", reply_markup=get_main_menu(True))
    else:
        await message.answer("⚠️ Xatolik: Buyurtma bazadan topilmadi.")

    await state.clear()


# 3. Admin "RAD ETISH" tugmasini bossa (Buyurtma uchun)
@router.callback_query(F.data.startswith("admin_reject_"))
async def reject_order_handler(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return

    order_id = callback.data.split("_")[2]
    
    # Bazada statusni o'zgartirish
    db.db.reject_order(order_id)
    
    # Xabarni o'zgartirib qo'yish
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n❌ <b>BEKOR QILINDI</b>",
        reply_markup=None, 
        parse_mode="HTML"
    )
    
    # Mijozga xabar berish
    order = db.db.get_order(order_id)
    if order:
        user_id = order[1]
        try:
            await bot.send_message(user_id, f"❌ Sizning #{order_id} buyurtmangiz bekor qilindi.\nQo'shimcha ma'lumot uchun admin bilan bog'laning.")
        except:
            pass
            
    await callback.answer("❌ Buyurtma bekor qilindi", show_alert=True)


# ==================================================
# 🔥 FIREBASE: KURSLAR UCHUN TO'LOV TASDIQLASH 🔥
# ==================================================

# 1. Admin "✅ Tasdiqlash" ni bossa (KURS uchun)
@router.callback_query(F.data.startswith("pay_confirm_"))
async def approve_payment_handler(callback: CallbackQuery):
    # Emailni ajratib olish
    user_email = callback.data.split("_")[2]
    
    admin_msg = ""
    try:
        # Userni email orqali qidiramiz
        users_ref = db_firebase.collection('users')
        query = users_ref.where('email', '==', user_email).get()

        if query:
            # Agar user topilsa, unga kursni qo'shamiz
            user_doc = query[0]
            user_doc.reference.update({
                'ownedCourses': firestore.ArrayUnion(['pinduoduo-pro']) 
            })
            admin_msg = "✅ Kurs ochildi (Firebase bazaga yozildi)."
        else:
            # Agar user bazada bo'lmasa, yangi ochib qo'yamiz
            users_ref.add({
                'email': user_email,
                'ownedCourses': ['pinduoduo-pro'],
                'role': 'student'
            })
            admin_msg = "✅ Yangi user yaratildi va kurs ochildi."
            
    except Exception as e:
        print(f"Firebase xatosi: {e}")
        admin_msg = f"⚠️ Baza xatosi: {e}"

    # Xabarni tahrirlash
    original_caption = callback.message.caption
    new_caption = f"{original_caption}\n\n✅ <b>QABUL QILINDI!</b>\n{admin_msg}"

    await callback.message.edit_caption(
        caption=new_caption,
        parse_mode="HTML",
        reply_markup=None 
    )
    await callback.answer("✅ To'lov tasdiqlandi!")


# 2. Admin "❌ Bekor qilish" ni bossa (KURS uchun)
@router.callback_query(F.data == "pay_reject")
async def reject_payment_handler(callback: CallbackQuery):
    original_caption = callback.message.caption
    new_caption = f"{original_caption}\n\n❌ <b>TO'LOV RAD ETILDI!</b>\nChek yaroqsiz yoki noto'g'ri."

    await callback.message.edit_caption(
        caption=new_caption,
        parse_mode="HTML",
        reply_markup=None 
    )
    
    await callback.answer("❌ To'lov bekor qilindi", show_alert=True)