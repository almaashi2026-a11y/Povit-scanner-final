import time
import json
import logging
from datetime import datetime, timedelta

import config
from finnhub_client import client
from market_filter import market_filter
from pivot_detector import pivot_detector
from scoring import score_engine
from telegram_bot import telegram_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("scanner.log"), logging.StreamHandler()]
)


class StateManager:
    def __init__(self, file="state.json"):
        self.file = file
        self.state = self.load()

    def load(self):
        try:
            with open(self.file, "r") as f:
                return json.load(f)
        except Exception:
            return {"last_index": 0, "last_alerts": {}, "symbols": []}

    def save(self):
        with open(self.file, "w") as f:
            json.dump(self.state, f, indent=2)

    def get_index(self):
        return self.state.get("last_index", 0)

    def set_index(self, idx):
        self.state["last_index"] = idx
        self.save()

    def get_symbols(self):
        return self.state.get("symbols", [])

    def set_symbols(self, symbols):
        self.state["symbols"] = symbols
        self.save()

    def is_cooldown(self, symbol):
        last_alert = self.state["last_alerts"].get(symbol)
        if not last_alert:
            return False
        last_time = datetime.fromisoformat(last_alert)
        return datetime.utcnow() - last_time < timedelta(hours=config.COOLDOWN_HOURS)

    def update_alert(self, symbol):
        self.state["last_alerts"][symbol] = datetime.utcnow().isoformat()
        self.save()


class PivotScanner:
    def __init__(self):
        self.state = StateManager()
        self.symbols = self.load_symbols()

    def load_symbols(self):
        symbols = self.state.get_symbols()
        if symbols:
            return symbols
        logging.info("Fetching US symbol list from Finnhub...")
        symbols = client.get_us_symbols()
        if not symbols:
            logging.error("Failed to fetch symbols, using fallback list")
            symbols = ["AAPL", "TSLA", "AMD", "PLTR", "SOFI"]
        self.state.set_symbols(symbols)
        return symbols

    def process_symbol(self, symbol):
        try:
            if self.state.is_cooldown(symbol):
                return None

            quote = client.get_quote(symbol)
            if not quote:
                return None

            price = quote.get("c", 0)
            if not market_filter.quick_price_check(price):
                return None

            to_time = int(time.time())
            from_time = to_time - (45 * 24 * 60 * 60)
            candles = client.get_candles(symbol, "D", from_time, to_time)

            if not market_filter.is_valid_stock(candles):
                return None

            closes, highs = candles["c"], candles["h"]
            lows, volumes = candles["l"], candles["v"]

            is_pivot, pivot_data = pivot_detector.detect_pivot(closes, highs, lows, volumes)
            if not is_pivot:
                return None

            volume = volumes[-1]
            avg_volume = pivot_data.get("avg_volume", 0)
            score = score_engine.calculate(pivot_data, price, volume, avg_volume)

            if score < config.MIN_SCORE:
                return None

            return {"symbol": symbol, "score": score, "price": price, "pivot": pivot_data}

        except Exception as e:
            logging.error(f"Error processing {symbol}: {e}")
            return None

    def send_alert(self, result):
        symbol, price, score = result["symbol"], result["price"], result["score"]
        pivot = result["pivot"]
        message = (
            f"🎯 <b>إشارة ارتكاز</b>\n\n"
            f"📊 السهم: {symbol}\n"
            f"💰 السعر: {price}$\n"
            f"⭐ السكور: {score}/100\n"
            f"📉 نطاق الارتكاز: {pivot['pivot_range']}%\n"
            f"💧 جفاف الفوليوم: {'نعم' if pivot['volume_dry'] else 'لا'}\n"
            f"⏱ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        telegram_bot.send(message)
        self.state.update_alert(symbol)

    def run_batch(self):
        start_index = self.state.get_index()
        end_index = start_index + config.BATCH_SIZE
        batch = self.symbols[start_index:end_index]

        if not batch:
            logging.info("Restarting symbol cycle...")
            start_index, end_index = 0, config.BATCH_SIZE
            batch = self.symbols[start_index:end_index]

        logging.info(f"Processing batch {start_index} → {end_index} of {len(self.symbols)}")

        for i, symbol in enumerate(batch, start=start_index):
            result = self.process_symbol(symbol)
            if result:
                logging.info(f"Signal: {result}")
                self.send_alert(result)
            self.state.set_index(i + 1)
            time.sleep(config.REQUEST_DELAY)

    def run(self):
        logging.info("PivotScanner V2 Started 🚀")
        telegram_bot.send("✅ ماسح الارتكاز نشط الآن ويفحص السوق (0.20$ - 10$)")
        while True:
            try:
                self.run_batch()
                time.sleep(config.BATCH_DELAY)
            except Exception as e:
                logging.error(f"Main loop error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    scanner = PivotScanner()
    scanner.run()
