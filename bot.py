import asyncio
import logging
import sys

# Aiogram kutubxonasi
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperty
from aiogram.enums import ParseMode

# Ichki fayllar
from config import BOT_TOKEN
from database import init_db
from keep_alive import keep_alive # Render uchun

# Routerlarni (bo'limlarni) import qilish
from admin import router as admin_router
from user import router as user_router
from products import router as products_router
from cart import router as cart_router

async def main():
    # 1. Loglarni sozlash (Xatolarni ko'rish uchun)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # 2. Render serverida bot o'chib qolmasligi uchun soxta serverni yoqish
    try:
        keep_alive()
        logging.info("✅ Keep-alive serveri ishga tushdi.")
    except Exception as e:
        logging.error(f"❌ Keep-alive xatosi: {e}")

    # 3. Ma'lumotlar bazasini tekshirish va yaratish
    try:
        await init_db()
        logging.info("✅ Ma'lumotlar bazasi tayyor.")
    except Exception as e:
        logging.error(f"❌ Bazani ishga tushirishda xato: {e}")
        return

    # 4. Bot va Dispatcher obyektlarini yaratish
    # DefaultBotProperty orqali hamma xabarlarni HTML formatida yuborishni sozlaymiz
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperty(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # 5. Routerlarni ulash (TARTIB MUHIM!)
    # Eslatma: Admin router birinchi turishi kerak, keyin do'kon qismlari, oxirida user router
    dp.include_routers(
        admin_router,     # Admin paneli buyruqlari
        products_router,  # Mahsulotlarni ko'rish va varaqlash
        cart_router,      # Savat va buyurtma berish
        user_router       # Start va asosiy menyu
    )

    # 6. Botni ishga tushirish (Polling)
    logging.info("🚀 Bot polling rejimida ishga tushdi!")
    
    # Eskidan qolib ketgan xabarlarni tozalab yuboramiz
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Bot ishlashida jiddiy xato: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("👋 Bot to'xtatildi.")