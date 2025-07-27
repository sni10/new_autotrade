import pytest
import asyncio
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.domain.entities.deal import Deal
from src.domain.entities.order import Order
from src.domain.entities.currency_pair import CurrencyPair
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.repositories.postgresql.postgresql_deals_repository import PostgreSQLDealsRepository

@pytest.fixture(scope="module")
async def db_manager():
    """Инициализирует менеджер БД, создает схему и очищает ее после тестов."""
    config = {
        "type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "user": "user",
        "password": "password",
        "database": "autotrade"
    }
    manager = DatabaseManager(config)
    initialized = await manager.initialize()
    if not initialized:
        pytest.fail("Не удалось подключиться к базе данных PostgreSQL.")

    # Создаем схему перед тестами
    schema_created = await manager.create_schema()
    if not schema_created:
        pytest.fail("Не удалось создать схему базы данных.")

    yield manager

    # Закрываем соединение после всех тестов
    await manager.close()

@pytest.mark.asyncio
async def test_save_and_get_deal(db_manager):
    """Тест сохранения и последующей проверки сделки в БД."""
    # 1. Подготовка
    repo = PostgreSQLDealsRepository(db_manager)
    await db_manager.execute_command("DELETE FROM deals") # Очищаем таблицу перед тестом

    buy_order = Order(order_id=1, side="BUY", order_type="LIMIT", price=50000, amount=0.001, symbol="BTCUSDT")
    currency_pair = CurrencyPair(symbol="BTCUSDT", base_currency="BTC", quote_currency="USDT")
    deal = Deal(
        deal_id=123,
        currency_pair=currency_pair,
        buy_order=buy_order,
        status="ACTIVE",
        created_at=datetime.now()
    )

    # 2. Выполнение
    success = await repo.save_deal(deal)

    # 3. Проверка
    assert success is True

    # Проверяем, что сделка действительно сохранилась в базе
    result = await db_manager.execute_query("SELECT * FROM deals WHERE id = $1", (deal.deal_id,))
    assert len(result) == 1
    saved_deal = result[0]
    assert saved_deal['id'] == deal.deal_id
    assert saved_deal['symbol'] == "BTCUSDT"
    assert saved_deal['status'] == "ACTIVE"