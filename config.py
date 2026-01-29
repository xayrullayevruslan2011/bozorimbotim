"""
Konfiguratsiya fayli - Bot sozlamalari
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot tokeni
BOT_TOKEN = "8543158894:AAHkaN83tLCgNrJ-Omutn744aTui784GScc"

# Admin ID (bir nechta admin bo'lishi mumkin)
ADMIN_IDS = [8215056224]  # O'zingizning Telegram ID'laringizni kiriting

# Admin bilan aloqa
ADMIN_USERNAME = "@Ruslanbek20119"  # Admin username

# Kanal (agar kerak bo'lsa)
CHANNEL_ID = "https://t.me/xitoybozor_n1"
# ... tepadagi kodlar ...

# Kanallar ro'yxati (Majburiy obuna uchun)
REQUIRED_CHANNELS = [
    "@xitoybozor_n1", 
    "@xitoydarslik_navoiy"
]