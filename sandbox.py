# sandbox.py (или main.py)
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
import logging

logger = logging.getLogger(__name__)

def main():
    cp = CurrencyPair(base_currency="BTC", quote_currency="USDT")

    # Репозитории
    deals_repo = InMemoryDealsRepository()
    orders_repo = InMemoryOrdersRepository()

    # Фабрика
    deal_factory = DealFactory()

    # 1) Создаём сделку
    deal = deal_factory.create_new_deal(cp)
    logger.info("New Deal: %s", deal)

    # 2) Сохраняем сделку
    deals_repo.save(deal)
    # Также сохраним оба ордера
    if deal.buy_order:
        orders_repo.save(deal.buy_order)
    if deal.sell_order:
        orders_repo.save(deal.sell_order)

    # 3) Проверим get_all_by_deal:
    buy_and_sell = orders_repo.get_all_by_deal(deal.deal_id)
    logger.info("Orders for this deal: %s", buy_and_sell)

    # 4) Закроем сделку
    deal.close()
    deals_repo.save(deal)  # сохраним статус
    logger.info("Closed deal: %s", deal)

if __name__ == "__main__":
    main()
