# sandbox.py (просто тестовый запуск)
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.deals_repository import InMemoryDealsRepository

def main():
    # 1) Создадим CurrencyPair
    cp = CurrencyPair(base_currency="BTC", quote_currency="USDT")

    # 2) Инициализируем фабрику сделок
    deal_factory = DealFactory()

    # 3) Создадим сделку
    deal = deal_factory.create_new_deal(cp)
    print("New Deal:", deal)

    # 4) Сохраним сделку в InMemoryDealsRepository
    deals_repo = InMemoryDealsRepository()
    deals_repo.save(deal)

    # 5) Получим её обратно
    same_deal = deals_repo.get_by_id(deal.deal_id)
    print("Fetched from repo:", same_deal)

    # 6) Проверим статус
    same_deal.close()  # закроем сделку
    print("Closed:", same_deal)

if __name__ == "__main__":
    main()
