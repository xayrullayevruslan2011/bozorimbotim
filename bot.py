import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from keep_alive import keep_alive
import database  # <--- MANA SHU QATOR BO'LISHI SHART!
import user, admin, cart, products

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def main():
    # 1. Serverni ishga tushirish
    keep_alive()

    # 2. BAZANI YARATISH (Bu bo'lmasa bot ishlamaydi!)
    try:
        await database.init_db()
        logger.info("✅ Baza yaratildi!")
    except Exception as e:
        logger.error(f"❌ Baza xatosi: {e}")
    
    # 3. Routerlarni ulash
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(cart.router)
    dp.include_router(products.router)

    # 4. Eski webhooklarni o'chirish
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 5. Botni ishga tushirish
    logger.info("Bot ishga tushdi... 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")