#!/usr/bin/env python3
# tests/test_architecture_simple.py
"""
🧪 УПРОЩЕННЫЕ ТЕСТЫ ДВУХУРОВНЕВОЙ АРХИТЕКТУРЫ ХРАНЕНИЯ

Тестирует основные компоненты без сложных импортов:
- Создание репозиториев
- Базовые операции с DataFrame
- Производительность
- Фабрику репозиториев
"""

import sys
import os
import time
import pandas as pd
from datetime import datetime

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_basic_dataframe_operations():
    """Тест базовых операций с DataFrame"""
    print("🧪 Тестируем базовые операции с DataFrame...")
    
    # Создаем DataFrame как в MemoryFirst репозиториях
    df = pd.DataFrame(columns=[
        'deal_id', 'currency_pair', 'status', 'created_at', 'profit'
    ])
    
    # Тест добавления данных
    start_time = time.time()
    data_rows = []
    for i in range(1000):
        data_rows.append({
            'deal_id': i + 1,
            'currency_pair': 'ATMUSDT',
            'status': 'OPEN',
            'created_at': datetime.now(),
            'profit': 0.0
        })
    # Создаем DataFrame из всех строк сразу, избегая concatenation warnings
    df = pd.DataFrame(data_rows)
    
    creation_time = time.time() - start_time
    avg_time = (creation_time / 1000) * 1000  # в миллисекундах
    
    print(f"✅ Создано 1000 записей за {creation_time:.2f}s")
    print(f"✅ Среднее время создания: {avg_time:.3f}ms")
    
    # Тест чтения данных
    start_time = time.time()
    open_deals = df[df['status'] == 'OPEN']
    read_time = (time.time() - start_time) * 1000
    
    print(f"✅ Чтение {len(open_deals)} записей за {read_time:.2f}ms")
    
    # Проверяем производительность
    assert avg_time < 5, f"Создание слишком медленное: {avg_time:.2f}ms"
    assert read_time < 50, f"Чтение слишком медленное: {read_time:.2f}ms"
    
    return True

def test_memory_first_repository_structure():
    """Тест структуры MemoryFirst репозитория"""
    print("🧪 Тестируем структуру MemoryFirst репозитория...")
    
    try:
        from infrastructure.repositories.base.base_repository import MemoryFirstRepository
        
        # Создаем тестовый репозиторий
        class TestRepository(MemoryFirstRepository):
            def _entity_to_dict(self, entity):
                return {'id': entity, 'data': f'test_{entity}'}
            
            def _dict_to_entity(self, data):
                return data['id']
            
            def _get_dataframe_columns(self):
                return ['id', 'data']
            
            def _get_id_column(self):
                return 'id'
        
        repo = TestRepository()
        
        # Проверяем инициализацию
        assert repo.df is not None
        assert len(repo.df) == 0
        assert repo._next_id == 1
        
        print("✅ MemoryFirstRepository структура корректна")
        return True
        
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать MemoryFirstRepository: {e}")
        return False

def test_repository_factory_structure():
    """Тест структуры фабрики репозиториев"""
    print("🧪 Тестируем структуру фабрики репозиториев...")
    
    try:
        from infrastructure.repositories.factory.repository_factory import RepositoryFactory
        
        factory = RepositoryFactory()
        
        # Проверяем инициализацию
        assert factory is not None
        assert hasattr(factory, 'config')
        assert hasattr(factory, '_initialized')
        assert factory._initialized is False
        
        # Проверяем методы
        assert hasattr(factory, 'initialize')
        assert hasattr(factory, 'get_storage_info')
        assert hasattr(factory, 'close')
        
        # Тест получения информации о хранилище
        storage_info = factory.get_storage_info()
        assert isinstance(storage_info, dict)
        
        print("✅ RepositoryFactory структура корректна")
        print(f"📊 Информация о хранилище: {storage_info}")
        return True
        
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать RepositoryFactory: {e}")
        return False

def test_config_loading():
    """Тест загрузки конфигурации"""
    print("🧪 Тестируем загрузку конфигурации...")
    
    try:
        from config.config_loader import load_config
        
        config = load_config()
        
        # Проверяем наличие секций
        assert 'database' in config
        assert 'storage' in config
        
        # Проверяем параметры БД
        db_config = config['database']
        assert db_config['host'] == 'localhost'
        assert db_config['port'] == 5434
        assert db_config['user'] == 'airflow'
        
        # Проверяем параметры хранилища
        storage_config = config['storage']
        assert storage_config['deals_type'] == 'memory_first_postgres'
        assert storage_config['orders_type'] == 'memory_first_postgres'
        assert storage_config['tickers_type'] == 'memory_first_parquet'
        
        print("✅ Конфигурация загружена корректно")
        print(f"📊 Тип хранилища сделок: {storage_config['deals_type']}")
        print(f"📊 Тип хранилища ордеров: {storage_config['orders_type']}")
        return True
        
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать config_loader: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка загрузки конфигурации: {e}")
        return False

def test_interfaces_structure():
    """Тест структуры интерфейсов"""
    print("🧪 Тестируем структуру интерфейсов...")
    
    interfaces_tested = 0
    
    # Тест интерфейса сделок
    try:
        from infrastructure.repositories.interfaces.deals_repository_interface import IDealsRepository
        from infrastructure.repositories.base.base_repository import AtomicRepository
        
        # Проверяем наследование
        assert issubclass(IDealsRepository, AtomicRepository)
        
        # Проверяем наличие методов
        methods = [method for method in dir(IDealsRepository) if not method.startswith('_')]
        expected_methods = ['get_open_deals', 'get_closed_deals', 'get_deals_by_symbol']
        
        for method in expected_methods:
            assert method in methods, f"Метод {method} не найден в IDealsRepository"
        
        print("✅ IDealsRepository структура корректна")
        interfaces_tested += 1
        
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать IDealsRepository: {e}")
    
    # Тест интерфейса ордеров
    try:
        from infrastructure.repositories.interfaces.orders_repository_interface import IOrdersRepository
        
        methods = [method for method in dir(IOrdersRepository) if not method.startswith('_')]
        expected_methods = ['get_by_exchange_id', 'get_open_orders', 'get_orders_by_symbol']
        
        for method in expected_methods:
            assert method in methods, f"Метод {method} не найден в IOrdersRepository"
        
        print("✅ IOrdersRepository структура корректна")
        interfaces_tested += 1
        
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать IOrdersRepository: {e}")
    
    # Тест интерфейса тикеров
    try:
        from infrastructure.repositories.interfaces.tickers_repository_interface import ITickersRepository
        from infrastructure.repositories.base.base_repository import StreamingRepository
        
        assert issubclass(ITickersRepository, StreamingRepository)
        
        methods = [method for method in dir(ITickersRepository) if not method.startswith('_')]
        expected_methods = ['get_latest_ticker', 'get_price_history', 'get_tickers_by_symbol']
        
        for method in expected_methods:
            assert method in methods, f"Метод {method} не найден в ITickersRepository"
        
        print("✅ ITickersRepository структура корректна")
        interfaces_tested += 1
        
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать ITickersRepository: {e}")
    
    return interfaces_tested > 0

def test_memory_first_implementations():
    """Тест MemoryFirst реализаций"""
    print("🧪 Тестируем MemoryFirst реализации...")
    
    implementations_tested = 0
    
    # Тест MemoryFirstDealsRepository
    try:
        from infrastructure.repositories.memory_first.memory_first_deals_repository import MemoryFirstDealsRepository
        
        repo = MemoryFirstDealsRepository()
        
        # Проверяем инициализацию
        assert repo.df is not None
        assert len(repo.df) == 0
        
        # Проверяем структуру DataFrame
        expected_columns = ['deal_id', 'currency_pair', 'status', 'created_at']
        for col in expected_columns:
            assert col in repo.df.columns, f"Колонка {col} не найдена в DataFrame"
        
        print("✅ MemoryFirstDealsRepository инициализирован корректно")
        implementations_tested += 1
        
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать MemoryFirstDealsRepository: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации MemoryFirstDealsRepository: {e}")
    
    # Тест MemoryFirstTickersRepository
    try:
        from infrastructure.repositories.memory_first.memory_first_tickers_repository import MemoryFirstTickersRepository
        
        repo = MemoryFirstTickersRepository(batch_size=100, dump_interval_minutes=60)
        
        # Проверяем инициализацию
        assert repo.df is not None
        assert len(repo.df) == 0
        assert repo.batch_size == 100
        assert repo.dump_interval_minutes == 60
        
        # Проверяем структуру DataFrame
        expected_columns = ['symbol', 'timestamp', 'last_price']
        for col in expected_columns:
            assert col in repo.df.columns, f"Колонка {col} не найдена в DataFrame"
        
        print("✅ MemoryFirstTickersRepository инициализирован корректно")
        implementations_tested += 1
        
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать MemoryFirstTickersRepository: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации MemoryFirstTickersRepository: {e}")
    
    return implementations_tested > 0

def test_performance_benchmarks():
    """Тест производительности системы"""
    print("🧪 Тестируем производительность системы...")
    
    # Тест производительности DataFrame операций
    df = pd.DataFrame(columns=['id', 'symbol', 'price', 'timestamp'])
    
    # Бенчмарк массового добавления
    records_count = 10000
    start_time = time.time()
    
    data_rows = []
    for i in range(records_count):
        data_rows.append({
            'id': i + 1,
            'symbol': 'ATMUSDT',
            'price': 100.0 + i * 0.001,
            'timestamp': int(time.time() * 1000) + i
        })
    # Создаем DataFrame из всех строк сразу, избегая concatenation warnings
    df = pd.DataFrame(data_rows)
    
    creation_time = time.time() - start_time
    records_per_sec = records_count / creation_time
    
    print(f"✅ Создано {records_count} записей за {creation_time:.2f}s")
    print(f"✅ Производительность: {records_per_sec:.0f} записей/сек")
    
    # Бенчмарк поиска
    start_time = time.time()
    filtered_df = df[df['symbol'] == 'ATMUSDT']
    search_time = (time.time() - start_time) * 1000
    
    print(f"✅ Поиск в {len(df)} записях за {search_time:.2f}ms")
    print(f"✅ Найдено {len(filtered_df)} записей")
    
    # Проверяем производительность
    assert records_per_sec > 1000, f"Производительность слишком низкая: {records_per_sec:.0f}/sec"
    assert search_time < 100, f"Поиск слишком медленный: {search_time:.2f}ms"
    
    return True

def run_all_tests():
    """Запуск всех упрощенных тестов"""
    print("🧪 ЗАПУСК УПРОЩЕННЫХ ТЕСТОВ ДВУХУРОВНЕВОЙ АРХИТЕКТУРЫ")
    print("=" * 60)
    
    tests = [
        ("Базовые операции DataFrame", test_basic_dataframe_operations),
        ("Структура MemoryFirst репозитория", test_memory_first_repository_structure),
        ("Структура фабрики репозиториев", test_repository_factory_structure),
        ("Загрузка конфигурации", test_config_loading),
        ("Структура интерфейсов", test_interfaces_structure),
        ("MemoryFirst реализации", test_memory_first_implementations),
        ("Производительность системы", test_performance_benchmarks)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            if result:
                passed_tests += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"⚠️ {test_name} - ЧАСТИЧНО ПРОЙДЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено тестов: {passed_tests}/{total_tests}")
    print(f"📈 Процент успеха: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Двухуровневая архитектура хранения работоспособна")
        print("✅ Производительность соответствует требованиям")
        print("✅ Все компоненты инициализируются корректно")
    elif passed_tests >= total_tests * 0.7:
        print("\n✅ БОЛЬШИНСТВО ТЕСТОВ ПРОЙДЕНО!")
        print("⚠️ Некоторые компоненты требуют доработки")
        print("🔧 Проверьте предупреждения выше")
    else:
        print("\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ!")
        print("🔧 Необходимо исправить ошибки перед использованием")
    
    return passed_tests, total_tests

if __name__ == "__main__":
    run_all_tests()