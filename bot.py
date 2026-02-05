import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db

# Barcha bo'limlarni (routerlarni) chaqiramiz
from admin import router as admin_router
from user import router as user_router
from products import router as products_router
from cart import router as cart_router

async def main():
    # Loglarni yoqish
    logging.basicConfig(level=logging.INFO)
    
    # Bazani ishga tushirish
    await init_db()
    
    # Bot va Dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # ⚠️ MUHIM: Routerlarni ro'yxatdan o'tkazish tartibi
    # (products_router va cart_router qo'shilgan bo'lishi shart!)
    dp.include_routers(
        admin_router,     # 1. Admin buyruqlari
        products_router,  # 2. Mahsulotlar bo'limi (Sizda shu yetishmayotgan edi)
        cart_router,      # 3. Savat bo'limi
        user_router       # 4. Asosiy user menyusi (eng oxirida turgani ma'qul)
    )

    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi")