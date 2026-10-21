import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
TON_WALLET = os.getenv("TON_WALLET")

STAR_BUY_RATE = 0.012
STAR_SELL_RATE = 0.0154

MIN_BUY = 50
MAX_BUY = 50000
MIN_SELL = 50
MAX_SELL = 100000

SUPPORT_USERNAME = "@ton_support"
CHANNEL = "@ton_channel"
