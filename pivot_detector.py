import numpy as np
from config import PIVOT_RANGE


class PivotDetector:
    def detect_pivot(self, closes, highs, lows, volumes):
        if len(closes) < 20:
            return False, {}

        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        pivot_range = (recent_high - recent_low) / recent_high

        recent_volume = np.mean(volumes[-5:])
        previous_volume = np.mean(volumes[-20:-5])
        volume_dry = recent_volume < previous_volume

        is_pivot = pivot_range <= PIVOT_RANGE and volume_dry

        result = {
            "pivot": is_pivot,
            "pivot_high": recent_high,
            "pivot_low": recent_low,
            "pivot_range": round(pivot_range * 100, 2),
            "volume_dry": volume_dry,
            "avg_volume": round(previous_volume, 0)
        }
        return is_pivot, result


pivot_detector = PivotDetector()
