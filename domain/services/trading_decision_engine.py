# domain/services/trading_decision_engine.py
from typing import Dict, Optional
from .orderbook_analyzer import OrderBookAnalyzer, OrderBookMetrics, OrderBookSignal

class TradingDecisionEngine:
    """Движок принятия торговых решений с учетом MACD + стакана"""
    
    def __init__(self, orderbook_analyzer: OrderBookAnalyzer):
        self.orderbook_analyzer = orderbook_analyzer
        
    def should_execute_trade(self, macd_signal: bool, orderbook_metrics: OrderBookMetrics) -> Dict:
        """Принятие решения о выполнении сделки"""
        
        result = {
            'execute': False,
            'reason': '',
            'confidence': 0,
            'modifications': {}
        }
        
        # Проверка сигнала стакана
        if orderbook_metrics.signal == OrderBookSignal.REJECT:
            result['reason'] = f"❌ СТАКАН: Отклонено (спред: {orderbook_metrics.bid_ask_spread:.3f}%, слиппедж: {orderbook_metrics.slippage_buy:.2f}%)"
            return result
            
        # Базовый MACD сигнал
        if not macd_signal:
            result['reason'] = "❌ MACD: Нет сигнала"
            return result
            
        # Анализ комбинированного сигнала
        if orderbook_metrics.signal in [OrderBookSignal.STRONG_BUY, OrderBookSignal.WEAK_BUY]:
            result['execute'] = True
            result['confidence'] = orderbook_metrics.confidence
            
            # Модификации на основе стакана
            modifications = {}
            
            # Корректировка цены входа по поддержке
            if orderbook_metrics.support_level:
                modifications['entry_price_hint'] = orderbook_metrics.support_level
                
            # Корректировка цены выхода по сопротивлению  
            if orderbook_metrics.resistance_level:
                modifications['exit_price_hint'] = orderbook_metrics.resistance_level
                
            # Корректировка размера позиции при высоком слиппедже
            if orderbook_metrics.slippage_buy > 0.5:
                modifications['reduce_position_size'] = 0.7  # Уменьшить на 30%
                
            result['modifications'] = modifications
            
            # Формирование описания
            signal_emoji = "🟢🔥" if orderbook_metrics.signal == OrderBookSignal.STRONG_BUY else "🟡"
            result['reason'] = f"{signal_emoji} СТАКАН ПОДДЕРЖИВАЕТ: {orderbook_metrics.signal.value} (доверие: {orderbook_metrics.confidence:.1%})"
            
        elif orderbook_metrics.signal == OrderBookSignal.NEUTRAL:
            result['execute'] = True  # Нейтральный стакан не мешает MACD
            result['confidence'] = 0.6
            result['reason'] = "🟡 СТАКАН НЕЙТРАЛЕН: MACD решает"
            
        else:  # WEAK_SELL, STRONG_SELL
            result['reason'] = f"❌ СТАКАН ПРОТИВ: {orderbook_metrics.signal.value} (дисбаланс: {orderbook_metrics.volume_imbalance:.1f}%)"
            
        return result
    
    def format_orderbook_info(self, metrics: OrderBookMetrics) -> str:
        """Форматирование информации о стакане"""
        info = []
        info.append(f"📊 АНАЛИЗ СТАКАНА:")
        info.append(f"   💱 Спред: {metrics.bid_ask_spread:.3f}%")
        info.append(f"   ⚖️ Дисбаланс: {metrics.volume_imbalance:+.1f}% {'(покупатели)' if metrics.volume_imbalance > 0 else '(продавцы)'}")
        info.append(f"   💧 Ликвидность: {metrics.liquidity_depth:.1f}")
        info.append(f"   📉 Слиппедж покупки: {metrics.slippage_buy:.2f}%")
        info.append(f"   📈 Слиппедж продажи: {metrics.slippage_sell:.2f}%")
        
        if metrics.support_level:
            info.append(f"   🛡️ Поддержка: {metrics.support_level:.4f}")
        if metrics.resistance_level:
            info.append(f"   🚧 Сопротивление: {metrics.resistance_level:.4f}")
            
        if metrics.big_walls:
            info.append(f"   🧱 Больших стен: {len(metrics.big_walls)}")
            
        return "\n".join(info)
    
    def apply_orderbook_modifications(self, current_price: float, budget: float, modifications: Dict) -> Dict:
        """Применение модификаций от анализа стакана к расчету сделки"""
        
        result = {
            'entry_price': current_price,
            'budget_multiplier': 1.0,
            'exit_price_hint': None,
            'modifications_applied': []
        }
        
        # Применение модификаций от стакана
        if 'entry_price_hint' in modifications:
            hint_price = modifications['entry_price_hint']
            # Используем рекомендуемую цену, если она лучше текущей
            if hint_price < current_price:  # Лучшая цена для покупки
                result['entry_price'] = hint_price
                result['modifications_applied'].append(f"💡 Используем цену поддержки: {hint_price:.4f} вместо {current_price:.4f}")
        
        # Корректировка размера позиции
        if 'reduce_position_size' in modifications:
            result['budget_multiplier'] = modifications['reduce_position_size']
            result['modifications_applied'].append(f"⚠️ Уменьшаем размер позиции до {result['budget_multiplier']:.1%}")
            
        # Целевая цена выхода
        if 'exit_price_hint' in modifications:
            result['exit_price_hint'] = modifications['exit_price_hint']
            result['modifications_applied'].append(f"💡 Целевая цена сопротивления: {result['exit_price_hint']:.4f}")
            
        return result
