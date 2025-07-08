# domain/services/orderbook_analyzer.py
import asyncio
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class OrderBookSignal(Enum):
    """Сигналы от анализа стакана"""
    STRONG_BUY = "strong_buy"
    WEAK_BUY = "weak_buy" 
    NEUTRAL = "neutral"
    WEAK_SELL = "weak_sell"
    STRONG_SELL = "strong_sell"
    REJECT = "reject"  # Отклонить сделку

@dataclass
class OrderBookMetrics:
    """Метрики стакана"""
    bid_ask_spread: float
    bid_volume: float
    ask_volume: float
    volume_imbalance: float  # % покупателей - продавцов
    liquidity_depth: float
    support_level: Optional[float]
    resistance_level: Optional[float]
    slippage_buy: float
    slippage_sell: float
    big_walls: List[Dict]
    signal: OrderBookSignal
    confidence: float  # 0-1

class OrderBookAnalyzer:
    """Анализатор биржевого стакана"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.min_volume_threshold = config.get('min_volume_threshold', 1000)
        self.big_wall_threshold = config.get('big_wall_threshold', 5000)
        self.max_spread_percent = config.get('max_spread_percent', 0.5)
        self.min_liquidity_depth = config.get('min_liquidity_depth', 10)
        self.typical_order_size = config.get('typical_order_size', 10)  # USDT
        
    async def get_orderbook_stream(self, exchange, symbol: str):
        """Получение потока данных стакана через вебсокет"""
        try:
            while True:
                orderbook = await exchange.watch_order_book(symbol)
                metrics = self.analyze_orderbook(orderbook)
                yield metrics
                await asyncio.sleep(0.1)  # Небольшая задержка
                
        except Exception as e:
            logger.error(f"Ошибка получения стакана: {e}")
            
    def analyze_orderbook(self, orderbook: Dict) -> OrderBookMetrics:
        """Полный анализ стакана"""
        bids = orderbook['bids']
        asks = orderbook['asks']
        
        if not bids or not asks:
            return self._create_reject_metrics("Пустой стакан")
            
        # Базовые метрики
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        spread = best_ask - best_bid
        spread_percent = (spread / best_bid) * 100
        
        # Объемы
        bid_volume = sum([bid[1] for bid in bids[:self.min_liquidity_depth]])
        ask_volume = sum([ask[1] for ask in asks[:self.min_liquidity_depth]])
        total_volume = bid_volume + ask_volume
        volume_imbalance = ((bid_volume - ask_volume) / total_volume) * 100 if total_volume > 0 else 0
        
        # Анализ ликвидности
        liquidity_depth = self._calculate_liquidity_depth(bids, asks, best_bid)
        
        # Поддержка и сопротивление
        support_level = self._find_support_level(bids)
        resistance_level = self._find_resistance_level(asks)
        
        # Слиппедж
        slippage_buy = self._calculate_slippage(asks, 'buy')
        slippage_sell = self._calculate_slippage(bids, 'sell')
        
        # Большие стены
        big_walls = self._find_big_walls(bids, asks)
        
        # Генерация сигнала
        signal, confidence = self._generate_signal(
            spread_percent, volume_imbalance, liquidity_depth,
            slippage_buy, slippage_sell, big_walls
        )
        
        return OrderBookMetrics(
            bid_ask_spread=spread_percent,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            volume_imbalance=volume_imbalance,
            liquidity_depth=liquidity_depth,
            support_level=support_level,
            resistance_level=resistance_level,
            slippage_buy=slippage_buy,
            slippage_sell=slippage_sell,
            big_walls=big_walls,
            signal=signal,
            confidence=confidence
        )
    
    def _calculate_liquidity_depth(self, bids: List, asks: List, mid_price: float) -> float:
        """Расчет глубины ликвидности в % от цены"""
        total_volume = 0
        price_range = 0
        
        # Анализ бидов
        for bid in bids:
            if bid[0] > mid_price * 0.95:  # В пределах 5% от цены
                total_volume += bid[1]
                price_range = max(price_range, abs(bid[0] - mid_price))
                
        # Анализ асков
        for ask in asks:
            if ask[0] < mid_price * 1.05:  # В пределах 5% от цены
                total_volume += ask[1]
                price_range = max(price_range, abs(ask[0] - mid_price))
                
        return total_volume / max(price_range, 0.001)
    
    def _find_support_level(self, bids: List) -> Optional[float]:
        """Поиск уровня поддержки"""
        if len(bids) < 5:
            return None
            
        # Ищем самый большой объем в бидах
        max_volume = 0
        support_price = None
        
        for bid in bids[:20]:  # Анализируем топ-20
            if bid[1] > max_volume:
                max_volume = bid[1]
                support_price = bid[0]
                
        return support_price if max_volume > self.big_wall_threshold else None
    
    def _find_resistance_level(self, asks: List) -> Optional[float]:
        """Поиск уровня сопротивления"""
        if len(asks) < 5:
            return None
            
        # Ищем самый большой объем в асках
        max_volume = 0
        resistance_price = None
        
        for ask in asks[:20]:  # Анализируем топ-20
            if ask[1] > max_volume:
                max_volume = ask[1]
                resistance_price = ask[0]
                
        return resistance_price if max_volume > self.big_wall_threshold else None
    
    def _calculate_slippage(self, orders: List, side: str) -> float:
        """Расчет слиппеджа для объема сделки"""
        volume_to_execute = self.typical_order_size  # USDT
        
        cumulative_volume = 0
        weighted_price = 0
        
        for order in orders:
            price, volume = order[0], order[1]
            
            if side == 'buy':
                order_value = price * volume
            else:
                order_value = price * volume
                
            if cumulative_volume + order_value >= volume_to_execute:
                # Частичное исполнение последнего ордера
                remaining = volume_to_execute - cumulative_volume
                weighted_price += price * remaining
                cumulative_volume += remaining
                break
            else:
                # Полное исполнение ордера
                weighted_price += price * order_value
                cumulative_volume += order_value
                
        if cumulative_volume > 0:
            avg_price = weighted_price / cumulative_volume
            best_price = orders[0][0]
            return abs((avg_price - best_price) / best_price) * 100
        
        return 999  # Недостаточно ликвидности
    
    def _find_big_walls(self, bids: List, asks: List) -> List[Dict]:
        """Поиск больших стен в стакане"""
        big_walls = []
        
        # Анализ бидов
        for bid in bids:
            if bid[1] > self.big_wall_threshold:
                big_walls.append({
                    'side': 'bid',
                    'price': bid[0],
                    'volume': bid[1],
                    'type': 'support'
                })
                
        # Анализ асков
        for ask in asks:
            if ask[1] > self.big_wall_threshold:
                big_walls.append({
                    'side': 'ask',
                    'price': ask[0],
                    'volume': ask[1],
                    'type': 'resistance'
                })
                
        return big_walls
    
    def _generate_signal(self, spread_percent: float, volume_imbalance: float, 
                        liquidity_depth: float, slippage_buy: float, 
                        slippage_sell: float, big_walls: List) -> Tuple[OrderBookSignal, float]:
        """Генерация сигнала на основе всех метрик"""
        
        # Проверки на отклонение сделки
        if spread_percent > self.max_spread_percent:
            return OrderBookSignal.REJECT, 0.9
            
        if slippage_buy > 2.0 or slippage_sell > 2.0:
            return OrderBookSignal.REJECT, 0.8
            
        if liquidity_depth < self.min_liquidity_depth:
            return OrderBookSignal.REJECT, 0.7
        
        # Подсчет очков для сигнала
        score = 0
        confidence = 0.5
        
        # Дисбаланс объемов
        if volume_imbalance > 20:  # Больше покупателей
            score += 2
            confidence += 0.2
        elif volume_imbalance > 10:
            score += 1
            confidence += 0.1
        elif volume_imbalance < -20:  # Больше продавцов
            score -= 2
            confidence += 0.2
        elif volume_imbalance < -10:
            score -= 1
            confidence += 0.1
            
        # Анализ больших стен
        resistance_walls = [w for w in big_walls if w['type'] == 'resistance']
        support_walls = [w for w in big_walls if w['type'] == 'support']
        
        if len(support_walls) > len(resistance_walls):
            score += 1
            confidence += 0.1
        elif len(resistance_walls) > len(support_walls):
            score -= 1
            confidence += 0.1
            
        # Ликвидность
        if liquidity_depth > self.min_liquidity_depth * 2:
            score += 1
            confidence += 0.1
            
        # Слиппедж
        if slippage_buy < 0.1 and slippage_sell < 0.1:
            score += 1
            confidence += 0.1
            
        # Преобразование в сигнал
        if score >= 3:
            return OrderBookSignal.STRONG_BUY, min(confidence, 0.95)
        elif score >= 1:
            return OrderBookSignal.WEAK_BUY, min(confidence, 0.8)
        elif score <= -3:
            return OrderBookSignal.STRONG_SELL, min(confidence, 0.95)
        elif score <= -1:
            return OrderBookSignal.WEAK_SELL, min(confidence, 0.8)
        else:
            return OrderBookSignal.NEUTRAL, confidence
    
    def _create_reject_metrics(self, reason: str) -> OrderBookMetrics:
        """Создание метрик с сигналом отклонения"""
        return OrderBookMetrics(
            bid_ask_spread=999,
            bid_volume=0,
            ask_volume=0,
            volume_imbalance=0,
            liquidity_depth=0,
            support_level=None,
            resistance_level=None,
            slippage_buy=999,
            slippage_sell=999,
            big_walls=[],
            signal=OrderBookSignal.REJECT,
            confidence=0.9
        )
