class ScoreEngine:
    def calculate(self, pivot_data, price, volume, avg_volume):
        score = 0

        if pivot_data["pivot"]:
            score += 35
        if pivot_data["volume_dry"]:
            score += 20
        if pivot_data["pivot_range"] <= 3:
            score += 20
        elif pivot_data["pivot_range"] <= 5:
            score += 10
        if volume >= 1000000:
            score += 15
        elif volume >= 500000:
            score += 10
        elif volume >= 300000:
            score += 5
        if avg_volume > 0:
            ratio = volume / avg_volume
            if ratio >= 3:
                score += 10
            elif ratio >= 2:
                score += 7
            elif ratio >= 1.5:
                score += 5

        return min(score, 100)


score_engine = ScoreEngine()
