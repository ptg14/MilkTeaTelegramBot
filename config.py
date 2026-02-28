import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID", "")

SHOP_NAME = "Trà Sữa Việt"
SHOP_ADDRESS = "123 Nguyễn Huệ, Q1"
SHOP_PHONE = "0909 123 456"
WORKING_HOURS = "8:00 - 22:00"
MENU_FILE = "Menu.csv"

WELCOME_MESSAGE = f"""
🧋 *Chào mừng đến {SHOP_NAME}!*

Bot đặt đồ uống tự động 24/7 🤖

📍 {SHOP_ADDRESS}
📞 {SHOP_PHONE}
🕐 {WORKING_HOURS}

Chọn menu bên dưới để bắt đầu!
"""
