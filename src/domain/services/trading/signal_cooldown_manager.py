# domain/services/signal_cooldown_manager.py
from typing import Tuple

class SignalCooldownManager:
    """
    Защита от повторных сигналов BUY:
    - Только лимит активных сделок (без проверки цены)
    """
    
    def __init__(self):
        pass  # Убираем все переменные связанные с ценой
        
    def can_buy(self, active_deals_count: int, max_deals: int) -> Tuple[bool, str]:
        """
        Проверяет, можно ли выдать сигнал BUY
        
        Args:
            active_deals_count: Количество активных сделок
            max_deals: Максимальное количество сделок (deal_count)
            
        Returns:
            (can_buy: bool, reason: str)
        """
        
        # Проверка лимита сделок
        if active_deals_count >= max_deals:
            return False, f"🎯 Лимит сделок: {active_deals_count}/{max_deals}"

        return True, "✅ Можно покупать"
    
    def get_status(self, active_deals_count: int, max_deals: int) -> str:
        """
        Возвращает текущий статус менеджера
        """
        return f"🎯 Активных сделок: {active_deals_count}/{max_deals}"
