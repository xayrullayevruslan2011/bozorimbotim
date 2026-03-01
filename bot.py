import asyncio
import logging
import sys

# Aiogram kutubxonasi
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties # 's' harfi qo'shildi
from aiogram.enums import ParseMode

# Ichki fayllar
from config import BOT_TOKEN
from database import init_db
from keep_alive import keep_alive # Render uchun

# Routerlarni (bo'limlarni) import qilish
from admin import router as admin_router
from user import router as user_router


async def main():
    # 1. Loglarni sozlash
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # 2. Render port xatosini oldini olish uchun Flask server
    keep_alive()

    # 3. Ma'lumotlar bazasini tekshirish
    await init_db()

    # 4. Bot va Dispatcher obyektlari
    # 'DefaultBotProperties' (plural) ishlatildi
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # 5. Routerlarni ulash
    dp.include_routers(
        admin_router,
        user_router
    )

    # 6. Botni ishga tushirish
    await bot.delete_webhook(drop_pending_updates=True)
    
    logging.info("🚀 Bot Render serverida muvaffaqiyatli ishga tushdi!")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Bot ishlashida xato: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())