import requests
import time
import logging
from config import FINNHUB_API_KEY

BASE_URL = "https://finnhub.io/api/v1"


class FinnhubClient:
    def __init__(self):
        self.api_key = FINNHUB_API_KEY

    def _request(self, endpoint, params=None):
        if params is None:
            params = {}
        params["token"] = self.api_key
        url = f"{BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print("⚠️ Rate Limit... waiting")
                time.sleep(3)
                return None
            else:
                print(f"HTTP Error: {response.status_code} | {response.text[:200]}")
                return None
        except Exception as e:
            print("Connection Error:", e)
            return None

    def get_quote(self, symbol):
        return self._request("quote", {"symbol": symbol})

    def get_candles(self, symbol, resolution, start, end):
        return self._request("stock/candle", {
            "symbol": symbol, "resolution": resolution,
            "from": start, "to": end
        })

    def get_us_symbols(self, retries=3, delay=5):
        """
        يجيب قائمة كل أسهم NASDAQ/NYSE من Finnhub.
        يحاول عدة مرات بفاصل زمني قبل ما يستسلم، ويطبع سبب الفشل الحقيقي.
        """
        for attempt in range(1, retries + 1):
            logging.info(f"Fetching US symbol list from Finnhub (attempt {attempt}/{retries})...")
            data = self._request("stock/symbol", {"exchange": "US"})
            if data:
                symbols = [s["symbol"] for s in data if s.get("type") == "Common Stock"]
                if symbols:
                    logging.info(f"Fetched {len(symbols)} symbols from Finnhub")
                    return symbols
            logging.warning(f"Attempt {attempt} failed to fetch symbols")
            if attempt < retries:
                time.sleep(delay)
        return []


client = FinnhubClient()
