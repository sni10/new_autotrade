from typing import List, Dict
import statistics


class MarketAnalysisService:
    """🔍 Сервис для анализа рыночных условий"""

    def __init__(self):
        self.analysis_window = 20

    def analyze_volatility(self, prices: List[float]) -> Dict:
        """Подробный анализ волатильности"""
        if len(prices) < self.analysis_window:
            return {"status": "insufficient_data", "message": "Недостаточно данных"}

        recent_prices = prices[-self.analysis_window:]

        # Вычисляем различные метрики волатильности
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = (recent_prices[i] - recent_prices[i - 1]) / recent_prices[i - 1]
            price_changes.append(abs(change))

        avg_volatility = statistics.mean(price_changes) * 100
        max_volatility = max(price_changes) * 100
        volatility_std = statistics.stdev(price_changes) * 100 if len(price_changes) > 1 else 0

        # Классификация
        risk_level = self._classify_risk(avg_volatility)
        trading_recommendation = self._get_trading_recommendation(avg_volatility)

        return {
            "avg_volatility": round(avg_volatility, 3),
            "max_volatility": round(max_volatility, 3),
            "volatility_std": round(volatility_std, 3),
            "risk_level": risk_level,
            "trading_recommendation": trading_recommendation,
            "should_trade": 0.03 <= avg_volatility <= 0.12
        }

    def _classify_risk(self, volatility: float) -> str:
        """Классифицирует уровень риска"""
        if volatility > 0.15:
            return "🔥 ЭКСТРЕМАЛЬНЫЙ"
        elif volatility > 0.08:
            return "⚡ ВЫСОКИЙ"
        elif volatility > 0.03:
            return "📊 СРЕДНИЙ"
        else:
            return "😴 НИЗКИЙ"

    def _get_trading_recommendation(self, volatility: float) -> str:
        """Дает рекомендации по торговле"""
        if volatility > 0.15:
            return "❌ НЕ ТОРГОВАТЬ - слишком рискованно"
        elif volatility > 0.12:
            return "⚠️ ОСТОРОЖНО - высокий риск"
        elif volatility > 0.03:
            return "✅ МОЖНО ТОРГОВАТЬ"
        else:
            return "🟡 НИЗКАЯ АКТИВНОСТЬ - мало возможностей"

    def analyze_trend(self, prices: List[float], window: int = 10) -> Dict:
        """Анализ тренда"""
        if len(prices) < window:
            return {"status": "insufficient_data"}

        recent_prices = prices[-window:]
        first_price = recent_prices[0]
        last_price = recent_prices[-1]

        change_percent = (last_price - first_price) / first_price * 100

        # Считаем наклон тренда (линейная регрессия упрощенно)
        x_values = list(range(len(recent_prices)))
        slope = self._calculate_slope(x_values, recent_prices)

        trend_direction = "📈 ВОСХОДЯЩИЙ" if slope > 0 else "📉 НИСХОДЯЩИЙ" if slope < 0 else "➡️ БОКОВОЙ"

        return {
            "change_percent": round(change_percent, 2),
            "slope": round(slope, 6),
            "trend_direction": trend_direction,
            "strength": self._classify_trend_strength(abs(change_percent))
        }

    def _calculate_slope(self, x_values: List, y_values: List[float]) -> float:
        """Простой расчет наклона тренда"""
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope

    def _classify_trend_strength(self, change_percent: float) -> str:
        """Классифицирует силу тренда"""
        if change_percent > 2.0:
            return "🔥 СИЛЬНЫЙ"
        elif change_percent > 0.5:
            return "📊 УМЕРЕННЫЙ"
        else:
            return "😴 СЛАБЫЙ"
