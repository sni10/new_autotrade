# domain/services/deal_service.py

from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from infrastructure.repositories.interfaces.deals_repository_interface import IDealsRepository
from domain.services.orders.order_service import OrderService
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DealService:
    """
    Сервис для управления сделками:
    - Создание сделок через DealFactory,
    - Обновление и управление статусами сделок,
    - Взаимодействие с OrderService для управления ордерами.
    """

    def __init__(self, deals_repo: IDealsRepository, order_service: OrderService, deal_factory: DealFactory, exchange_connector: CcxtExchangeConnector):
        self.deals_repo = deals_repo
        self.order_service = order_service
        self.deal_factory = deal_factory
        self.exchange_connector = exchange_connector

    async def check_balance_before_deal(self, quote_currency: str, required_amount: float) -> (bool, str):
        """Проверяет, достаточно ли средств на балансе."""
        try:
            balance = await self.exchange_connector.get_balance(quote_currency)
            if balance >= required_amount:
                return True, f"Баланс {quote_currency} достаточен: {balance:.2f}"
            else:
                return False, f"Недостаточно средств. Требуется: {required_amount:.2f}, доступно: {balance:.2f}"
        except Exception as e:
            return False, f"Ошибка при проверке баланса: {e}"

    def create_new_deal(self, currency_pair: CurrencyPair) -> Deal:
        """
        Создает новую сделку для указанной валютной пары.
        """
        deal = self.deal_factory.create_new_deal(currency_pair)
        self.deals_repo.save(deal)
        logger.info(f"Created new deal: {deal}")
        return deal

    async def open_buy_order(self, symbol, price, amount, deal_id):
        """
        Создает BUY ордер и связывает его со сделкой.
        """
        result = await self.order_service.create_and_place_buy_order(
            symbol, amount, price, deal_id
        )
        if not result.success:
            logger.error(f"❌ Failed to create BUY order for deal {deal_id}: {result.error_message}")
            return None
        buy_order = result.order
        
        # Связываем ордер со сделкой
        deal = self.get_deal_by_id(deal_id)
        if deal:
            deal.buy_order = buy_order
            self.deals_repo.save(deal)  # Сохраняем обновленную сделку
            logger.info(f"✅ BUY Order linked to deal {deal_id}: {buy_order}")
        else:
            logger.warning(f"⚠️ Deal {deal_id} not found when linking BUY order")
        
        logger.info(f"Create BUY Order: {buy_order}")
        return buy_order


    async def open_sell_order(self, symbol, price, amount, deal_id):
        """
        Создает SELL ордер и связывает его со сделкой.
        """
        result = await self.order_service.create_local_sell_order(
            symbol, amount, price, deal_id
        )
        if not result.success:
            logger.error(f"❌ Failed to create SELL order for deal {deal_id}: {result.error_message}")
            return None
        sell_order = result.order
        
        # Связываем ордер со сделкой
        deal = self.get_deal_by_id(deal_id)
        if deal:
            deal.sell_order = sell_order
            self.deals_repo.save(deal)  # Сохраняем обновленную сделку
            logger.info(f"✅ SELL Order linked to deal {deal_id}: {sell_order}")
        else:
            logger.warning(f"⚠️ Deal {deal_id} not found when linking SELL order")
        
        logger.info(f"Create SELL Order: {sell_order}")
        return sell_order

    def process_open_deals(self):
        """
        Проверяет и обрабатывает все открытые сделки.
        """
        open_deals = self.deals_repo.get_open_deals()
        for deal in open_deals:
            if self.should_close_deal(deal):
                self.close_deal(deal)

    def close_deal(self, deal_id: int):
        """
        Закрывает сделку, меняя ее статус на CLOSED.
        """
        deal = self.get_deal_by_id(deal_id)
        if deal and deal.is_open():
            deal.close()
            self.deals_repo.save(deal)
            logger.info(f"Closed deal: {deal}")
        elif not deal:
            logger.warning(f"Попытка закрыть несуществующую сделку: {deal_id}")
        else:
            logger.info(f"Сделка {deal_id} уже закрыта, статус: {deal.status}")

    async def close_deal_if_completed(self, deal: Deal) -> bool:
        """
        Закрывает сделку если оба ордера исполнены.
        Возвращает True если сделка была закрыта.
        """
        # Проверяем статус ордеров
        if deal.buy_order:
            deal.buy_order = await self.order_service.get_order_status(deal.buy_order)
        if deal.sell_order:
            deal.sell_order = await self.order_service.get_order_status(deal.sell_order)
        
        # Если оба ордера исполнены - закрываем сделку естественно
        if (deal.buy_order and deal.buy_order.is_filled() and 
            deal.sell_order and deal.sell_order.is_filled()):
            
            # Рассчитываем прибыль
            buy_cost = deal.buy_order.calculate_total_cost_with_fees()
            sell_revenue = deal.sell_order.calculate_total_cost()
            profit = sell_revenue - buy_cost
            
            deal.close()
            self.deals_repo.save(deal)
            logger.info(f"✅ Deal completed naturally: {deal.deal_id}, profit: {profit:.4f} USDT")
            return True
        
        return False

    def should_close_deal(self, deal: Deal) -> bool:
        """
        Определяет, нужно ли закрывать сделку на основе бизнес-логики.
        """
        # Здесь может быть сложная логика с проверкой условий: времени, цен, индикаторов и т.п.
        return False  # Пример: возвращаем False, не закрываем автоматически

    def get_open_deals(self) -> List[Deal]:
        """
        Возвращает список всех открытых сделок.
        """
        return self.deals_repo.get_open_deals()

    def get_deal_by_id(self, deal_id: int) -> Optional[Deal]:
        """
        Возвращает сделку по идентификатору.
        """
        return self.deals_repo.get_by_id(deal_id)

    def force_close_all(self):
        """
        Принудительное закрытие всех открытых сделок.
        """
        for deal in self.get_open_deals():
            self.close_deal(deal)

    def get_statistics(self) -> dict:
        """
        Получение статистики сервиса сделок для SystemStatsMonitor
        """
        try:
            # Получаем все сделки из репозитория
            all_deals = self.deals_repo.get_all() if hasattr(self.deals_repo, 'get_all') else []
            open_deals = self.get_open_deals()
            
            # Подсчитываем завершенные сделки
            completed_deals = []
            if all_deals:
                completed_deals = [deal for deal in all_deals if deal.status == 'CLOSED' or not deal.is_open()]
            
            return {
                'total_deals': len(all_deals),
                'open_deals': len(open_deals),
                'completed_deals': len(completed_deals),
                'active_deals': len(open_deals)  # Дополнительная статистика
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики сделок: {e}")
            # Возвращаем базовую статистику в случае ошибки
            open_deals = self.get_open_deals()
            return {
                'total_deals': len(open_deals),  # Минимум что можем получить
                'open_deals': len(open_deals),
                'completed_deals': 0,
                'active_deals': len(open_deals)
            }
