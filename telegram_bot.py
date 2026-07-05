import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send(self, message):
        data = {"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}
        try:
            response = requests.post(self.url, data=data, timeout=15)
            if response.status_code == 200:
                print("✅ Telegram Alert Sent")
                return True
            print(response.text)
            return False
        except Exception as e:
            print("Telegram Error:", e)
            return False


telegram_bot = TelegramBot()
