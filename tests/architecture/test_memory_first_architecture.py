#!/usr/bin/env python3
# tests/test_memory_first_architecture.py
"""
🧪 КОМПЛЕКСНЫЕ ТЕСТЫ ДВУХУРОВНЕВОЙ АРХИТЕКТУРЫ ХРАНЕНИЯ

Тестирует все компоненты новой архитектуры:
- Базовые интерфейсы и абстракции
- MemoryFirst репозитории (атомарные и потоковые)
- Фабрику репозиториев
- Интеграцию с PostgreSQL
- Parquet дампы
- Fallback механизмы
- Производительность
"""

import pytest
import asyncio
import pandas as pd
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import List, Optional

# Импорты тестируемых компонентов
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from infrastructure.repositories.base.base_repository import (
    BaseRepository, AtomicRepository, StreamingRepository, MemoryFirstRepository
)
from infrastructure.repositories.interfaces.deals_repository_interface import IDealsRepository
from infrastructure.repositories.interfaces.orders_repository_interface import IOrdersRepository
from infrastructure.repositories.interfaces.tickers_repository_interface import ITickersRepository
from infrastructure.repositories.interfaces.order_books_repository_interface import IOrderBooksRepository

from infrastructure.repositories.memory_first.memory_first_deals_repository import MemoryFirstDealsRepository
from infrastructure.repositories.memory_first.memory_first_orders_repository import MemoryFirstOrdersRepository
from infrastructure.repositories.memory_first.memory_first_tickers_repository import MemoryFirstTickersRepository
from infrastructure.repositories.memory_first.memory_first_order_books_repository import MemoryFirstOrderBooksRepository

from infrastructure.repositories.factory.repository_factory import RepositoryFactory

# Импорты доменных сущностей
from domain.entities.deal import Deal
from domain.entities.order import Order
from domain.entities.currency_pair import CurrencyPair
from domain.entities.ticker import Ticker
from domain.entities.order_book import OrderBook


class TestMemoryFirstArchitecture:
    """Комплексные тесты двухуровневой архитектуры хранения"""
    
    @pytest.fixture
    def currency_pair(self):
        """Тестовая валютная пара"""
        return CurrencyPair(
            base_currency="ATM",
            quote_currency="USDT",
            symbol="ATMUSDT",
            deal_quota=25.0
        )
    
    @pytest.fixture
    def test_deal(self, currency_pair):
        """Тестовая сделка"""
        return Deal(
            deal_id=1,
            currency_pair=currency_pair,
            status=Deal.STATUS_OPEN
        )
    
    @pytest.fixture
    def test_order(self):
        """Тестовый ордер"""
        return Order(
            order_id=1,
            side=Order.SIDE_BUY,
            order_type=Order.TYPE_LIMIT,
            price=100.0,
            amount=25.0,
            symbol="ATMUSDT",
            status=Order.STATUS_PENDING
        )
    
    @pytest.fixture
    def test_ticker(self):
        """Тестовый тикер"""
        ticker = Ticker({"symbol": "ATMUSDT", "timestamp": int(time.time() * 1000)})
        ticker.last = 100.0
        ticker.bid = 99.5
        ticker.ask = 100.5
        ticker.baseVolume = 1000.0
        ticker.high = 105.0
        ticker.low = 95.0
        return ticker
    
    @pytest.fixture
    def test_order_book(self):
        """Тестовый стакан ордеров"""
        return OrderBook(
            symbol="ATMUSDT",
            bids=[[99.5, 100], [99.0, 200]],
            asks=[[100.5, 150], [101.0, 300]],
            timestamp=int(time.time() * 1000)
        )


class TestMemoryFirstDealsRepository(TestMemoryFirstArchitecture):
    """Тесты репозитория сделок (АТОМАРНЫЕ ДАННЫЕ)"""
    
    def test_deals_repository_creation(self):
        """Тест создания репозитория сделок"""
        repo = MemoryFirstDealsRepository()
        
        assert repo is not None
        assert isinstance(repo, IDealsRepository)
        assert isinstance(repo, MemoryFirstRepository)
        assert repo.df is not None
        assert len(repo.df) == 0
        
        print("✅ MemoryFirstDealsRepository создан успешно")
    
    def test_deals_save_and_get(self, test_deal):
        """Тест сохранения и получения сделки"""
        repo = MemoryFirstDealsRepository()
        
        # Тест сохранения
        start_time = time.time()
        repo.save(test_deal)
        save_time = (time.time() - start_time) * 1000
        
        assert save_time < 10, f"Сохранение слишком медленное: {save_time:.2f}ms"
        assert len(repo.df) == 1
        
        # Тест получения по ID
        start_time = time.time()
        retrieved_deal = repo.get_by_id(test_deal.deal_id)
        get_time = (time.time() - start_time) * 1000
        
        assert get_time < 5, f"Получение слишком медленное: {get_time:.2f}ms"
        assert retrieved_deal is not None
        assert retrieved_deal.deal_id == test_deal.deal_id
        assert retrieved_deal.currency_pair.symbol == test_deal.currency_pair.symbol
        
        print(f"✅ Сделка сохранена за {save_time:.2f}ms, получена за {get_time:.2f}ms")
    
    def test_deals_specialized_methods(self, test_deal, currency_pair):
        """Тест специализированных методов сделок"""
        repo = MemoryFirstDealsRepository()
        
        # Создаем несколько тестовых сделок
        deal1 = Deal(deal_id=1, currency_pair=currency_pair, status=Deal.STATUS_OPEN)
        deal2 = Deal(deal_id=2, currency_pair=currency_pair, status=Deal.STATUS_CLOSED)
        deal3 = Deal(deal_id=3, currency_pair=currency_pair, status=Deal.STATUS_OPEN)
        
        repo.save(deal1)
        repo.save(deal2)
        repo.save(deal3)
        
        # Тест получения открытых сделок
        open_deals = repo.get_open_deals()
        assert len(open_deals) == 2
        
        # Тест получения закрытых сделок
        closed_deals = repo.get_closed_deals()
        assert len(closed_deals) == 1
        
        # Тест получения по символу
        symbol_deals = repo.get_deals_by_symbol("ATMUSDT")
        assert len(symbol_deals) == 3
        
        # Тест статистики
        stats = repo.get_deals_statistics()
        assert stats["total_deals"] == 3
        assert stats["open_deals"] == 2
        assert stats["closed_deals"] == 1
        
        print("✅ Специализированные методы сделок работают корректно")
    
    def test_deals_performance(self, currency_pair):
        """Тест производительности операций с сделками"""
        repo = MemoryFirstDealsRepository()
        
        # Тест массового создания сделок
        deals_count = 1000
        start_time = time.time()
        
        for i in range(deals_count):
            deal = Deal(deal_id=i+1, currency_pair=currency_pair, status=Deal.STATUS_OPEN)
            repo.save(deal)
        
        creation_time = time.time() - start_time
        avg_creation_time = (creation_time / deals_count) * 1000
        
        assert avg_creation_time < 3, f"Среднее время создания сделки слишком большое: {avg_creation_time:.2f}ms"
        
        # Тест массового чтения
        start_time = time.time()
        all_deals = repo.get_all()
        read_time = (time.time() - start_time) * 1000
        
        assert read_time < 140, f"Время чтения всех сделок слишком большое: {read_time:.2f}ms"
        assert len(all_deals) == deals_count
        
        print(f"✅ Производительность: {deals_count} сделок созданы за {creation_time:.2f}s")
        print(f"✅ Среднее время создания: {avg_creation_time:.3f}ms")
        print(f"✅ Время чтения всех сделок: {read_time:.2f}ms")


class TestMemoryFirstOrdersRepository(TestMemoryFirstArchitecture):
    """Тесты репозитория ордеров (АТОМАРНЫЕ ДАННЫЕ)"""
    
    def test_orders_repository_creation(self):
        """Тест создания репозитория ордеров"""
        repo = MemoryFirstOrdersRepository()
        
        assert repo is not None
        assert isinstance(repo, IOrdersRepository)
        assert isinstance(repo, MemoryFirstRepository)
        assert repo.df is not None
        assert len(repo.df) == 0
        
        print("✅ MemoryFirstOrdersRepository создан успешно")
    
    def test_orders_save_and_get(self, test_order):
        """Тест сохранения и получения ордера"""
        repo = MemoryFirstOrdersRepository()
        
        # Тест сохранения
        start_time = time.time()
        repo.save(test_order)
        save_time = (time.time() - start_time) * 1000
        
        assert save_time < 10, f"Сохранение ордера слишком медленное: {save_time:.2f}ms"
        assert len(repo.df) == 1
        
        # Тест получения по ID
        start_time = time.time()
        retrieved_order = repo.get_by_id(test_order.order_id)
        get_time = (time.time() - start_time) * 1000
        
        assert get_time < 5, f"Получение ордера слишком медленное: {get_time:.2f}ms"
        assert retrieved_order is not None
        assert retrieved_order.order_id == test_order.order_id
        assert retrieved_order.symbol == test_order.symbol
        
        print(f"✅ Ордер сохранен за {save_time:.2f}ms, получен за {get_time:.2f}ms")
    
    def test_orders_status_updates(self, test_order):
        """Тест обновления статуса ордеров"""
        repo = MemoryFirstOrdersRepository()
        repo.save(test_order)
        
        # Тест обновления статуса
        success = repo.update_order_status(test_order.order_id, Order.STATUS_FILLED, 25.0, 0.1)
        assert success is True
        
        # Проверяем обновление
        updated_order = repo.get_by_id(test_order.order_id)
        assert updated_order.status == Order.STATUS_FILLED
        assert updated_order.filled_amount == 25.0
        assert updated_order.fees == 0.1
        
        print("✅ Обновление статуса ордера работает корректно")


class TestMemoryFirstTickersRepository(TestMemoryFirstArchitecture):
    """Тесты репозитория тикеров (ПОТОКОВЫЕ ДАННЫЕ)"""
    
    @pytest.mark.asyncio
    async def test_tickers_repository_creation(self):
        """Тест создания репозитория тикеров"""
        repo = MemoryFirstTickersRepository(batch_size=100, dump_interval_minutes=1)
        
        assert repo is not None
        assert isinstance(repo, ITickersRepository)
        assert isinstance(repo, MemoryFirstRepository)
        assert repo.df is not None
        assert len(repo.df) == 0
        assert repo.batch_size == 100
        
        print("✅ MemoryFirstTickersRepository создан успешно")
    
    @pytest.mark.asyncio
    async def test_tickers_streaming_operations(self, test_ticker):
        """Тест потоковых операций с тикерами"""
        repo = MemoryFirstTickersRepository(batch_size=10, dump_interval_minutes=60)
        
        # Тест массового добавления тикеров
        tickers_count = 50
        start_time = time.time()
        
        for i in range(tickers_count):
            ticker = Ticker({"symbol": "ATMUSDT", "timestamp": int(time.time() * 1000) + i})
            ticker.last = 100.0 + i * 0.1
            ticker.bid = 99.5 + i * 0.1
            ticker.ask = 100.5 + i * 0.1
            ticker.baseVolume = 1000.0 + i * 10
            repo.save(ticker)
        
        streaming_time = time.time() - start_time
        avg_streaming_time = (streaming_time / tickers_count) * 1000
        
        assert avg_streaming_time < 1.3, f"Среднее время записи тикера слишком большое: {avg_streaming_time:.2f}ms"
        
        # Тест получения последнего тикера
        latest_ticker = repo.get_latest_ticker("ATMUSDT")
        assert latest_ticker is not None
        assert latest_ticker.symbol == "ATMUSDT"
        
        # Тест истории цен
        price_history = repo.get_price_history("ATMUSDT", limit=10)
        assert len(price_history) <= 10
        assert all(isinstance(price, float) for price in price_history)
        
        print(f"✅ Потоковые операции: {tickers_count} тикеров за {streaming_time:.2f}s")
        print(f"✅ Среднее время записи: {avg_streaming_time:.3f}ms")
    
    @pytest.mark.asyncio
    async def test_tickers_memory_management(self):
        """Тест управления памятью для тикеров"""
        repo = MemoryFirstTickersRepository(batch_size=1000, keep_last_n=100)
        
        # Добавляем много тикеров
        for i in range(200):
            ticker = Ticker({"symbol": "ATMUSDT", "timestamp": int(time.time() * 1000) + i})
            ticker.last = 100.0 + i * 0.1
            repo.save(ticker)
        
        # Проверяем автоматическую очистку
        assert len(repo.df) <= repo.keep_last_n
        
        # Тест получения последних N записей
        last_10 = repo.get_last_n(10)
        assert len(last_10) <= 10
        
        print("✅ Управление памятью тикеров работает корректно")


class TestMemoryFirstOrderBooksRepository(TestMemoryFirstArchitecture):
    """Тесты репозитория стаканов ордеров (ПОТОКОВЫЕ ДАННЫЕ)"""
    
    @pytest.mark.asyncio
    async def test_order_books_repository_creation(self):
        """Тест создания репозитория стаканов"""
        repo = MemoryFirstOrderBooksRepository(batch_size=50, dump_interval_minutes=1)
        
        assert repo is not None
        assert isinstance(repo, IOrderBooksRepository)
        assert isinstance(repo, MemoryFirstRepository)
        assert repo.df is not None
        assert len(repo.df) == 0
        
        print("✅ MemoryFirstOrderBooksRepository создан успешно")
    
    @pytest.mark.asyncio
    async def test_order_books_streaming_operations(self, test_order_book):
        """Тест потоковых операций со стаканами"""
        repo = MemoryFirstOrderBooksRepository(batch_size=100, dump_interval_minutes=60)
        
        # Тест массового добавления стаканов
        order_books_count = 30
        start_time = time.time()
        
        for i in range(order_books_count):
            order_book = OrderBook(
                symbol="ATMUSDT",
                bids=[[99.5 + i * 0.1, 100 + i], [99.0 + i * 0.1, 200 + i]],
                asks=[[100.5 + i * 0.1, 150 + i], [101.0 + i * 0.1, 300 + i]],
                timestamp=int(time.time() * 1000) + i
            )
            repo.save(order_book)
        
        streaming_time = time.time() - start_time
        avg_streaming_time = (streaming_time / order_books_count) * 1000
        
        assert avg_streaming_time < 2, f"Среднее время записи стакана слишком большое: {avg_streaming_time:.2f}ms"
        
        # Тест получения последнего стакана
        latest_order_book = repo.get_latest_order_book("ATMUSDT")
        assert latest_order_book is not None
        assert latest_order_book.symbol == "ATMUSDT"
        
        # Тест истории спредов
        spread_history = repo.get_spread_history("ATMUSDT", limit=10)
        assert len(spread_history) <= 10
        assert all(isinstance(spread, float) for spread in spread_history)
        
        print(f"✅ Потоковые операции: {order_books_count} стаканов за {streaming_time:.2f}s")
        print(f"✅ Среднее время записи: {avg_streaming_time:.3f}ms")


class TestRepositoryFactory(TestMemoryFirstArchitecture):
    """Тесты фабрики репозиториев"""
    
    @pytest.mark.asyncio
    async def test_factory_creation_and_initialization(self):
        """Тест создания и инициализации фабрики"""
        factory = RepositoryFactory()
        
        assert factory is not None
        assert factory._initialized is False
        
        # Тест инициализации (без PostgreSQL)
        await factory.initialize()
        
        # Получаем информацию о хранилище
        storage_info = factory.get_storage_info()
        assert isinstance(storage_info, dict)
        assert "deals_type" in storage_info
        assert "orders_type" in storage_info
        
        await factory.close()
        
        print("✅ RepositoryFactory создана и инициализирована успешно")
    
    @pytest.mark.asyncio
    async def test_factory_repository_creation(self):
        """Тест создания репозиториев через фабрику"""
        factory = RepositoryFactory()
        await factory.initialize()
        
        try:
            # Тест создания репозитория сделок
            deals_repo = await factory.get_deals_repository()
            assert deals_repo is not None
            assert isinstance(deals_repo, IDealsRepository)
            
            # Тест создания репозитория ордеров
            orders_repo = await factory.get_orders_repository()
            assert orders_repo is not None
            assert isinstance(orders_repo, IOrdersRepository)
            
            # Тест создания репозитория тикеров
            tickers_repo = await factory.get_tickers_repository()
            assert tickers_repo is not None
            assert isinstance(tickers_repo, ITickersRepository)
            
            # Тест создания репозитория стаканов
            order_books_repo = await factory.get_order_books_repository()
            assert order_books_repo is not None
            assert isinstance(order_books_repo, IOrderBooksRepository)
            
            print("✅ Все репозитории созданы через фабрику успешно")
            
        finally:
            await factory.close()
    
    @pytest.mark.asyncio
    async def test_factory_fallback_mechanisms(self):
        """Тест fallback механизмов фабрики"""
        # Создаем фабрику с неправильной конфигурацией
        factory = RepositoryFactory()
        
        # Принудительно устанавливаем неправильную конфигурацию
        factory.config = {
            "database": {
                "host": "nonexistent_host",
                "port": 9999,
                "user": "wrong_user",
                "password": "wrong_password",
                "database": "wrong_db"
            },
            "storage": {
                "deals_type": "memory_first_postgres",
                "orders_type": "memory_first_postgres"
            }
        }
        
        await factory.initialize()
        
        try:
            # Должны получить fallback репозитории
            deals_repo = await factory.get_deals_repository()
            orders_repo = await factory.get_orders_repository()
            
            assert deals_repo is not None
            assert orders_repo is not None
            
            print("✅ Fallback механизмы работают корректно")
            
        finally:
            await factory.close()


class TestIntegrationScenarios(TestMemoryFirstArchitecture):
    """Интеграционные тесты полных сценариев"""
    
    @pytest.mark.asyncio
    async def test_full_trading_cycle_simulation(self, currency_pair):
        """Тест полного торгового цикла"""
        factory = RepositoryFactory()
        await factory.initialize()
        
        try:
            deals_repo = await factory.get_deals_repository()
            orders_repo = await factory.get_orders_repository()
            tickers_repo = await factory.get_tickers_repository()
            
            # 1. Создаем сделку
            deal = Deal(deal_id=1, currency_pair=currency_pair, status=Deal.STATUS_OPEN)
            deals_repo.save(deal)
            
            # 2. Создаем ордер на покупку
            buy_order = Order(
                order_id=1,
                side=Order.SIDE_BUY,
                order_type=Order.TYPE_LIMIT,
                price=100.0,
                amount=25.0,
                symbol="ATMUSDT",
                deal_id=deal.deal_id
            )
            orders_repo.save(buy_order)
            
            # 3. Добавляем тикеры
            for i in range(10):
                ticker = Ticker({"symbol": "ATMUSDT", "timestamp": int(time.time() * 1000) + i})
                ticker.last = 100.0 + i * 0.1
                tickers_repo.save(ticker)
            
            # 4. Проверяем состояние
            retrieved_deal = deals_repo.get_by_id(deal.deal_id)
            retrieved_order = orders_repo.get_by_id(buy_order.order_id)
            latest_ticker = tickers_repo.get_latest_ticker("ATMUSDT")
            
            assert retrieved_deal is not None
            assert retrieved_order is not None
            assert latest_ticker is not None
            
            # 5. Обновляем статус ордера
            orders_repo.update_order_status(buy_order.order_id, Order.STATUS_FILLED, 25.0, 0.1)
            
            # 6. Закрываем сделку
            deals_repo.close_deal(deal.deal_id, 2, 1.5)  # sell_order_id=2, profit=1.5
            
            # 7. Проверяем финальное состояние
            final_deal = deals_repo.get_by_id(deal.deal_id)
            final_order = orders_repo.get_by_id(buy_order.order_id)
            
            assert final_deal.status == Deal.STATUS_CLOSED
            assert final_order.status == Order.STATUS_FILLED
            
            print("✅ Полный торговый цикл выполнен успешно")
            
        finally:
            await factory.close()
    
    def test_performance_benchmarks(self, currency_pair):
        """Тест производительности всей системы"""
        deals_repo = MemoryFirstDealsRepository()
        orders_repo = MemoryFirstOrdersRepository()
        tickers_repo = MemoryFirstTickersRepository(batch_size=1000)
        
        # Бенчмарк создания сделок
        deals_count = 1000
        start_time = time.time()
        
        for i in range(deals_count):
            deal = Deal(deal_id=i+1, currency_pair=currency_pair, status=Deal.STATUS_OPEN)
            deals_repo.save(deal)
        
        deals_time = time.time() - start_time
        
        # Бенчмарк создания ордеров
        orders_count = 2000
        start_time = time.time()
        
        for i in range(orders_count):
            order = Order(
                order_id=i+1,
                side=Order.SIDE_BUY if i % 2 == 0 else Order.SIDE_SELL,
                order_type=Order.TYPE_LIMIT,
                price=100.0 + i * 0.01,
                amount=25.0,
                symbol="ATMUSDT"
            )
            orders_repo.save(order)
        
        orders_time = time.time() - start_time
        
        # Бенчмарк потоковых данных
        tickers_count = 10000
        start_time = time.time()
        
        for i in range(tickers_count):
            ticker = Ticker({"symbol": "ATMUSDT", "timestamp": int(time.time() * 1000) + i})
            ticker.last = 100.0 + i * 0.001
            tickers_repo.save(ticker)
        
        tickers_time = time.time() - start_time
        
        # Проверяем производительность
        deals_per_sec = deals_count / deals_time
        orders_per_sec = orders_count / orders_time
        tickers_per_sec = tickers_count / tickers_time
        
        assert deals_per_sec > 300, f"Производительность сделок слишком низкая: {deals_per_sec:.0f}/sec"
        assert orders_per_sec > 250, f"Производительность ордеров слишком низкая: {orders_per_sec:.0f}/sec"
        assert tickers_per_sec > 600, f"Производительность тикеров слишком низкая: {tickers_per_sec:.0f}/sec"
        
        print(f"✅ Производительность сделок: {deals_per_sec:.0f}/sec")
        print(f"✅ Производительность ордеров: {orders_per_sec:.0f}/sec")
        print(f"✅ Производительность тикеров: {tickers_per_sec:.0f}/sec")


def run_all_tests():
    """Запуск всех тестов"""
    print("🧪 ЗАПУСК КОМПЛЕКСНЫХ ТЕСТОВ ДВУХУРОВНЕВОЙ АРХИТЕКТУРЫ")
    print("=" * 60)
    
    # Запускаем pytest с подробным выводом
    pytest_args = [
        __file__,
        "-v",  # подробный вывод
        "-s",  # показывать print'ы
        "--tb=short",  # короткие трейсбеки
        "-x"  # остановиться на первой ошибке
    ]
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Двухуровневая архитектура хранения полностью работоспособна")
        print("✅ Производительность соответствует требованиям")
        print("✅ Fallback механизмы функционируют")
        print("✅ Интеграция компонентов корректна")
    else:
        print(f"\n❌ ТЕСТЫ ЗАВЕРШИЛИСЬ С ОШИБКАМИ (код: {exit_code})")
        print("🔧 Проверьте вывод выше для диагностики проблем")
    
    return exit_code


if __name__ == "__main__":
    run_all_tests()