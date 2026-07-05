from config import MIN_PRICE, MAX_PRICE, MIN_VOLUME, MIN_DOLLAR_VOLUME


class MarketFilter:
    def quick_price_check(self, price):
        if not price:
            return False
        return MIN_PRICE <= price <= MAX_PRICE

    def is_valid_stock(self, candles):
        if not candles or candles.get("s") != "ok":
            return False
        closes = candles.get("c", [])
        volumes = candles.get("v", [])
        if len(closes) == 0 or len(volumes) == 0:
            return False
        price = closes[-1]
        volume = volumes[-1]
        if price < MIN_PRICE or price > MAX_PRICE:
            return False
        if volume < MIN_VOLUME:
            return False
        if price * volume < MIN_DOLLAR_VOLUME:
            return False
        return True


market_filter = MarketFilter()
