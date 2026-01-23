"""
Ruslam|Market Bot
Asosiy bot fayli - barcha handlerlarni birlashtiradi
"""
from keep_alive import keep_alive
keep_alive()
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

# 1. KONFIGURATSIYANI BIRINCHI IMPORT QILING
from config import BOT_TOKEN 
from database import init_db

# 2. PROXY VA BOTNI TO'G'RI SOZLANG
# PythonAnywhere bepul tarifi uchun proxy shart

# Handlerlarni import qilish (DATABASE dan keyin bo'lishi xavfsizroq)
import user, products, cart, admin

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Botni ishga tushirish"""

    # BOT OBYEKTINI FAQAT BIR MARTA VA TO'G'RI SOZLAMALAR BILAN YARATING
    bot = Bot(
        token=BOT_TOKEN,
        await dp.start_polling(bot)
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Ma'lumotlar bazasini ishga tushirish
    logger.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor!")

    # Routerlarni qo'shish
    dp.include_router(user.router)
    dp.include_router(products.router)
    dp.include_router(cart.router)
    dp.include_router(admin.router)

    # Botni ishga tushirish
    logger.info("Bot ishga tushirilmoqda...")

    try:
        # Eski webhook-larni o'chirish
        await bot.delete_webhook(drop_pending_updates=True)

        # Polling rejimida ishga tushirish
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())