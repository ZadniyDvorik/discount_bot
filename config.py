import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
YANDEX_MAPS_API_KEY = os.getenv("YANDEX_MAPS_API_KEY")