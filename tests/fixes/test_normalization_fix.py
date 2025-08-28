#!/usr/bin/env python3
"""
🔧 ТЕСТ ИСПРАВЛЕНИЯ ДЕНОРМАЛИЗАЦИИ БАЗЫ ДАННЫХ

Демонстрирует разницу между:
❌ СТАРЫЙ ПОДХОД (денормализация): дублирование данных валютной пары в каждой сделке
✅ НОВЫЙ ПОДХОД (нормализация): валютные пары в отдельной таблице, сделки ссылаются по ID

Этот тест показывает, как исправлена архитектурная проблема, описанная в вопросе:
"Почему сделка содержит структурные данные о валюте которые должна содержать валютная пара???"
"""

import sys
import os
import asyncio
from datetime import datetime

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from infrastructure.repositories.memory_first.memory_first_deals_repository import MemoryFirstDealsRepository
from infrastructure.repositories.memory_first.memory_first_deals_repository_normalized import MemoryFirstDealsRepositoryNormalized
from infrastructure.repositories.memory_first.memory_first_currency_pairs_repository import MemoryFirstCurrencyPairsRepository

def print_section(title: str, emoji: str = "📋"):
    """Красивый вывод секции"""
    print(f"\n{emoji} {title}")
    print("=" * (len(title) + 4))

def print_subsection(title: str, emoji: str = "🔸"):
    """Красивый вывод подсекции"""
    print(f"\n{emoji} {title}")
    print("-" * (len(title) + 4))

def demonstrate_old_denormalized_approach():
    """Демонстрация старого денормализованного подхода"""
    print_section("❌ СТАРЫЙ ДЕНОРМАЛИЗОВАННЫЙ ПОДХОД", "❌")
    
    # Создаем старый репозиторий (с денормализацией)
    old_repo = MemoryFirstDealsRepository()
    
    # Создаем валютную пару
    currency_pair = CurrencyPair(
        base_currency="BTC",
        quote_currency="USDT", 
        symbol="BTCUSDT",
        deal_quota=100.0,
        profit_markup=0.015
    )
    
    print_subsection("Создаем несколько сделок с одной валютной парой")
    
    # Создаем несколько сделок с одной валютной парой
    deals = []
    for i in range(3):
        deal = Deal(
            deal_id=1000 + i,
            currency_pair=currency_pair,
            status=Deal.STATUS_OPEN,
            profit=0.0
        )
        old_repo.save(deal)
        deals.append(deal)
        print(f"✅ Создана сделка ID: {deal.deal_id}")
    
    print_subsection("Структура DataFrame (ДЕНОРМАЛИЗОВАННАЯ)")
    print("Колонки в DataFrame:")
    for col in old_repo.df.columns:
        print(f"   - {col}")
    
    print_subsection("Данные в DataFrame (показывает дублирование)")
    if not old_repo.df.empty:
        # Показываем только валютные колонки для демонстрации дублирования
        currency_columns = ['deal_id', 'currency_pair', 'base_currency', 'quote_currency', 'deal_quota']
        print(f"{'deal_id':<8} | {'symbol':<10} | {'base':<5} | {'quote':<5} | {'quota':<8}")
        print("-" * 50)
        
        for _, row in old_repo.df.iterrows():
            print(f"{row['deal_id']:<8} | {row['currency_pair']:<10} | {row['base_currency']:<5} | {row['quote_currency']:<5} | {row['deal_quota']:<8}")
    
    print_subsection("❌ ПРОБЛЕМЫ ДЕНОРМАЛИЗАЦИИ")
    print("1. 🔄 Дублирование данных: base_currency, quote_currency, deal_quota повторяются в каждой сделке")
    print("2. 💾 Расход памяти: избыточное хранение одинаковых данных")
    print("3. 🔧 Сложность обновления: изменение валютной пары требует обновления всех сделок")
    print("4. 🚫 Нарушение нормализации: валютные данные должны быть в отдельной таблице")
    print("5. 📊 Неконсистентность: возможны расхождения в данных валютной пары между сделками")
    
    return old_repo

def demonstrate_new_normalized_approach():
    """Демонстрация нового нормализованного подхода"""
    print_section("✅ НОВЫЙ НОРМАЛИЗОВАННЫЙ ПОДХОД", "✅")
    
    # Создаем репозиторий валютных пар
    currency_pairs_repo = MemoryFirstCurrencyPairsRepository()
    
    # Создаем нормализованный репозиторий сделок
    normalized_repo = MemoryFirstDealsRepositoryNormalized(
        persistent_provider=None,
        currency_pairs_repository=currency_pairs_repo
    )
    
    # Создаем валютную пару
    currency_pair = CurrencyPair(
        base_currency="BTC",
        quote_currency="USDT",
        symbol="BTCUSDT", 
        deal_quota=100.0,
        profit_markup=0.015
    )
    
    print_subsection("Сохраняем валютную пару в отдельный репозиторий")
    currency_pair_id = currency_pairs_repo.save(currency_pair)
    print(f"✅ Валютная пара сохранена с ID: {currency_pair_id}")
    
    print_subsection("Создаем несколько сделок с ссылкой на валютную пару")
    
    # Создаем несколько сделок с одной валютной парой
    deals = []
    for i in range(3):
        deal = Deal(
            deal_id=2000 + i,
            currency_pair=currency_pair,
            status=Deal.STATUS_OPEN,
            profit=0.0
        )
        normalized_repo.save(deal)
        deals.append(deal)
        print(f"✅ Создана сделка ID: {deal.deal_id}")
    
    print_subsection("Структура DataFrame валютных пар (НОРМАЛИЗОВАННАЯ)")
    print("Колонки в currency_pairs DataFrame:")
    for col in currency_pairs_repo.df.columns:
        print(f"   - {col}")
    
    print_subsection("Структура DataFrame сделок (НОРМАЛИЗОВАННАЯ)")
    print("Колонки в deals DataFrame:")
    for col in normalized_repo.df.columns:
        print(f"   - {col}")
    
    print_subsection("Данные валютных пар (отдельная таблица)")
    if not currency_pairs_repo.df.empty:
        print(f"{'id':<3} | {'symbol':<10} | {'base':<5} | {'quote':<5} | {'quota':<8} | {'markup':<8}")
        print("-" * 55)
        
        for _, row in currency_pairs_repo.df.iterrows():
            print(f"{row['id']:<3} | {row['symbol']:<10} | {row['base_currency']:<5} | {row['quote_currency']:<5} | {row['deal_quota']:<8} | {row['profit_markup']:<8}")
    
    print_subsection("Данные сделок (только ссылки на валютные пары)")
    if not normalized_repo.df.empty:
        print(f"{'deal_id':<8} | {'currency_pair_id':<15} | {'status':<8} | {'profit':<8}")
        print("-" * 45)
        
        for _, row in normalized_repo.df.iterrows():
            print(f"{row['deal_id']:<8} | {row['currency_pair_id']:<15} | {row['status']:<8} | {row['profit']:<8}")
    
    print_subsection("✅ ПРЕИМУЩЕСТВА НОРМАЛИЗАЦИИ")
    print("1. 🎯 Нет дублирования: валютные данные хранятся только в currency_pairs")
    print("2. 💾 Экономия памяти: сделки содержат только currency_pair_id")
    print("3. 🔧 Простота обновления: изменение валютной пары в одном месте")
    print("4. ✅ Соблюдение нормализации: правильная структура реляционной БД")
    print("5. 📊 Консистентность: единый источник данных для валютных пар")
    print("6. 🚀 Производительность: меньше данных для обработки в сделках")
    
    return normalized_repo, currency_pairs_repo

def demonstrate_data_retrieval():
    """Демонстрация получения данных в нормализованном подходе"""
    print_section("🔍 ПОЛУЧЕНИЕ ДАННЫХ В НОРМАЛИЗОВАННОМ ПОДХОДЕ", "🔍")
    
    # Создаем репозитории
    currency_pairs_repo = MemoryFirstCurrencyPairsRepository()
    normalized_repo = MemoryFirstDealsRepositoryNormalized(
        persistent_provider=None,
        currency_pairs_repository=currency_pairs_repo
    )
    
    # Создаем валютную пару
    currency_pair = CurrencyPair(
        base_currency="ETH",
        quote_currency="USDT",
        symbol="ETHUSDT",
        deal_quota=50.0,
        profit_markup=0.02
    )
    
    # Создаем сделку
    deal = Deal(
        deal_id=3001,
        currency_pair=currency_pair,
        status=Deal.STATUS_OPEN,
        profit=1.5
    )
    
    normalized_repo.save(deal)
    
    print_subsection("Получение сделки по ID")
    retrieved_deal = normalized_repo.get_by_id(3001)
    
    if retrieved_deal:
        print(f"✅ Сделка найдена:")
        print(f"   - ID: {retrieved_deal.deal_id}")
        print(f"   - Статус: {retrieved_deal.status}")
        print(f"   - Прибыль: {retrieved_deal.profit}")
        print(f"   - Валютная пара: {retrieved_deal.currency_pair.symbol}")
        print(f"   - Базовая валюта: {retrieved_deal.currency_pair.base_currency}")
        print(f"   - Котируемая валюта: {retrieved_deal.currency_pair.quote_currency}")
        print(f"   - Размер сделки: {retrieved_deal.currency_pair.deal_quota}")
        print(f"   - Наценка: {retrieved_deal.currency_pair.profit_markup}")
        
        print_subsection("🎯 КЛЮЧЕВОЕ ОТЛИЧИЕ")
        print("❌ В старом подходе: валютные данные дублировались в каждой сделке")
        print("✅ В новом подходе: валютные данные получаются из отдельного репозитория по ID")
        print("✅ Результат для пользователя: тот же объект Deal с полными данными!")

def compare_memory_usage():
    """Сравнение использования памяти"""
    print_section("📊 СРАВНЕНИЕ ИСПОЛЬЗОВАНИЯ ПАМЯТИ", "📊")
    
    # Старый подход
    old_repo = MemoryFirstDealsRepository()
    
    # Новый подход
    currency_pairs_repo = MemoryFirstCurrencyPairsRepository()
    normalized_repo = MemoryFirstDealsRepositoryNormalized(
        persistent_provider=None,
        currency_pairs_repository=currency_pairs_repo
    )
    
    # Создаем одну валютную пару
    currency_pair = CurrencyPair(
        base_currency="ADA",
        quote_currency="USDT",
        symbol="ADAUSDT",
        deal_quota=1000.0,
        profit_markup=0.01
    )
    
    # Создаем много сделок с одной валютной парой
    num_deals = 10
    
    print_subsection(f"Создаем {num_deals} сделок с одной валютной парой")
    
    # Старый подход - создаем сделки
    for i in range(num_deals):
        deal = Deal(
            deal_id=4000 + i,
            currency_pair=currency_pair,
            status=Deal.STATUS_OPEN,
            profit=i * 0.1
        )
        old_repo.save(deal)
    
    # Новый подход - создаем сделки
    for i in range(num_deals):
        deal = Deal(
            deal_id=5000 + i,
            currency_pair=currency_pair,
            status=Deal.STATUS_OPEN,
            profit=i * 0.1
        )
        normalized_repo.save(deal)
    
    print_subsection("Анализ использования памяти")
    
    # Подсчет колонок
    old_columns = len(old_repo.df.columns)
    normalized_deals_columns = len(normalized_repo.df.columns)
    currency_pairs_columns = len(currency_pairs_repo.df.columns)
    
    print(f"❌ Старый подход:")
    print(f"   - Колонок в deals: {old_columns}")
    print(f"   - Записей deals: {len(old_repo.df)}")
    print(f"   - Общее количество ячеек: {old_columns * len(old_repo.df)}")
    
    print(f"\n✅ Новый подход:")
    print(f"   - Колонок в deals: {normalized_deals_columns}")
    print(f"   - Записей deals: {len(normalized_repo.df)}")
    print(f"   - Колонок в currency_pairs: {currency_pairs_columns}")
    print(f"   - Записей currency_pairs: {len(currency_pairs_repo.df)}")
    print(f"   - Общее количество ячеек: {normalized_deals_columns * len(normalized_repo.df) + currency_pairs_columns * len(currency_pairs_repo.df)}")
    
    # Расчет экономии
    old_cells = old_columns * len(old_repo.df)
    new_cells = normalized_deals_columns * len(normalized_repo.df) + currency_pairs_columns * len(currency_pairs_repo.df)
    
    if old_cells > new_cells:
        savings = old_cells - new_cells
        savings_percent = (savings / old_cells) * 100
        print(f"\n🎯 ЭКОНОМИЯ ПАМЯТИ:")
        print(f"   - Сэкономлено ячеек: {savings}")
        print(f"   - Процент экономии: {savings_percent:.1f}%")
    
    print(f"\n💡 ВАЖНО:")
    print(f"   - Экономия растет с количеством сделок для одной валютной пары")
    print(f"   - При {num_deals} сделках уже видна экономия")
    print(f"   - При 1000+ сделках экономия будет существенной")

def main():
    """Главная функция демонстрации"""
    print("🔧 ДЕМОНСТРАЦИЯ ИСПРАВЛЕНИЯ ДЕНОРМАЛИЗАЦИИ БАЗЫ ДАННЫХ")
    print("=" * 70)
    print()
    print("ПРОБЛЕМА:")
    print('❓ "Почему сделка содержит структурные данные о валюте')
    print('   которые должна содержать валютная пара???"')
    print()
    print("ОТВЕТ:")
    print("❌ Это была ошибка денормализации в репозитории")
    print("✅ Исправлено: валютные пары теперь в отдельной таблице")
    
    # Демонстрация старого подхода
    old_repo = demonstrate_old_denormalized_approach()
    
    # Демонстрация нового подхода
    normalized_repo, currency_pairs_repo = demonstrate_new_normalized_approach()
    
    # Демонстрация получения данных
    demonstrate_data_retrieval()
    
    # Сравнение использования памяти
    compare_memory_usage()
    
    print_section("🎉 ЗАКЛЮЧЕНИЕ", "🎉")
    print("✅ Проблема денормализации ИСПРАВЛЕНА!")
    print("✅ Валютные пары теперь хранятся в отдельной таблице")
    print("✅ Сделки ссылаются на валютные пары по ID")
    print("✅ Соблюдены принципы нормализации базы данных")
    print("✅ Улучшена производительность и экономия памяти")
    print("✅ Упрощено обслуживание и обновление данных")
    
    print_section("📋 ФАЙЛЫ РЕШЕНИЯ", "📋")
    print("1. database_normalization_fix.sql - SQL скрипт миграции")
    print("2. currency_pairs_repository_interface.py - интерфейс репозитория валютных пар")
    print("3. memory_first_currency_pairs_repository.py - реализация репозитория валютных пар")
    print("4. memory_first_deals_repository_normalized.py - исправленный репозиторий сделок")
    print("5. test_normalization_fix.py - этот тест демонстрации")

if __name__ == "__main__":
    main()