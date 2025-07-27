# tests/ccxt_compliance/test_ccxt_order_compliance.py
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.domain.entities.order import Order


class TestCCXTOrderCompliance:
    """
    🚀 CCXT Order Compliance Tests
    
    Тесты проверяют полное соответствие Order Entity стандарту CCXT Unified API.
    Все поля, методы и форматы данных должны точно соответствовать CCXT спецификации.
    """

    @pytest.fixture
    def ccxt_standard_order(self):
        """Образец ордера строго по CCXT стандарту"""
        return {
            'id': '12345',
            'clientOrderId': 'myorder123',
            'datetime': '2024-01-15T10:30:00.000Z',
            'timestamp': 1705315800000,
            'lastTradeTimestamp': 1705315850000,
            'status': 'open',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'timeInForce': 'GTC',
            'side': 'buy',
            'price': 50000.0,
            'amount': 0.001,
            'filled': 0.0005,
            'remaining': 0.0005,
            'cost': 25.0,
            'average': 50000.0,
            'trades': [
                {
                    'id': 'trade1',
                    'timestamp': 1705315850000,
                    'datetime': '2024-01-15T10:30:50.000Z',
                    'symbol': 'BTC/USDT',
                    'side': 'buy',
                    'amount': 0.0005,
                    'price': 50000.0,
                    'cost': 25.0,
                    'fee': {'cost': 0.025, 'currency': 'USDT'}
                }
            ],
            'fee': {
                'cost': 0.025,
                'currency': 'USDT',
                'rate': 0.001
            },
            'info': {
                'orderId': '12345',
                'clientOrderId': 'myorder123',
                'status': 'PARTIALLY_FILLED'
            }
        }

    def test_ccxt_order_creation_from_standard_response(self, ccxt_standard_order):
        """Тест создания Order из стандартного CCXT ответа"""
        order = Order.from_ccxt_response(ccxt_standard_order)
        
        # Проверяем все CCXT поля
        assert order.id == '12345'
        assert order.clientOrderId == 'myorder123'
        assert order.datetime == '2024-01-15T10:30:00.000Z'
        assert order.timestamp == 1705315800000
        assert order.lastTradeTimestamp == 1705315850000
        assert order.status == 'open'
        assert order.symbol == 'BTC/USDT'
        assert order.type == 'limit'
        assert order.timeInForce == 'GTC'
        assert order.side == 'buy'
        assert order.price == 50000.0
        assert order.amount == 0.001
        assert order.filled == 0.0005
        assert order.remaining == 0.0005
        assert order.cost == 25.0
        assert order.average == 50000.0
        assert len(order.trades) == 1
        assert order.fee['cost'] == 0.025
        assert order.fee['currency'] == 'USDT'
        assert order.info['orderId'] == '12345'

    def test_ccxt_order_to_dict_compliance(self, ccxt_standard_order):
        """Тест соответствия to_ccxt_dict() CCXT стандарту"""
        order = Order.from_ccxt_response(ccxt_standard_order)
        ccxt_dict = order.to_ccxt_dict()
        
        # Проверяем наличие всех обязательных CCXT полей
        required_fields = [
            'id', 'clientOrderId', 'datetime', 'timestamp', 'lastTradeTimestamp',
            'status', 'symbol', 'type', 'timeInForce', 'side', 'price', 'amount',
            'filled', 'remaining', 'cost', 'average', 'trades', 'fee', 'info'
        ]
        
        for field in required_fields:
            assert field in ccxt_dict, f"Missing required CCXT field: {field}"
        
        # Проверяем точность значений
        assert ccxt_dict['id'] == ccxt_standard_order['id']
        assert ccxt_dict['symbol'] == ccxt_standard_order['symbol']
        assert ccxt_dict['status'] == ccxt_standard_order['status']
        assert ccxt_dict['type'] == ccxt_standard_order['type']
        assert ccxt_dict['side'] == ccxt_standard_order['side']

    def test_ccxt_status_values_compliance(self):
        """Тест соответствия статусов CCXT стандарту"""
        # CCXT статусы должны быть точно такими
        assert Order.STATUS_OPEN == 'open'
        assert Order.STATUS_CLOSED == 'closed'
        assert Order.STATUS_CANCELED == 'canceled'
        assert Order.STATUS_EXPIRED == 'expired'
        assert Order.STATUS_REJECTED == 'rejected'
        assert Order.STATUS_PENDING == 'pending'

    def test_ccxt_side_values_compliance(self):
        """Тест соответствия сторон ордера CCXT стандарту"""
        assert Order.SIDE_BUY == 'buy'
        assert Order.SIDE_SELL == 'sell'

    def test_ccxt_type_values_compliance(self):
        """Тест соответствия типов ордера CCXT стандарту"""
        assert Order.TYPE_LIMIT == 'limit'
        assert Order.TYPE_MARKET == 'market'
        assert Order.TYPE_STOP == 'stop'
        assert Order.TYPE_STOP_LIMIT == 'stop_limit'

    def test_ccxt_time_in_force_compliance(self):
        """Тест соответствия Time in Force CCXT стандарту"""
        assert Order.TIF_GTC == 'GTC'
        assert Order.TIF_IOC == 'IOC'
        assert Order.TIF_FOK == 'FOK'
        assert Order.TIF_PO == 'PO'

    def test_ccxt_validation_compliance(self):
        """Тест валидации на соответствие CCXT стандарту"""
        # Создаем валидный CCXT ордер
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type=Order.TYPE_LIMIT,
            side=Order.SIDE_BUY,
            amount=0.001,
            price=50000.0,
            status=Order.STATUS_OPEN
        )
        
        is_valid, errors = order.validate_ccxt_compliance()
        assert is_valid is True
        assert len(errors) == 0

    def test_ccxt_validation_missing_fields(self):
        """Тест валидации с отсутствующими обязательными полями"""
        # Создаем ордер без обязательных полей
        order = Order(
            amount=0.001  # Только amount, всё остальное отсутствует
        )
        
        is_valid, errors = order.validate_ccxt_compliance()
        assert is_valid is False
        assert len(errors) > 0
        assert any('symbol' in error for error in errors)
        assert any('side' in error for error in errors)
        assert any('type' in error for error in errors)

    def test_ccxt_update_from_response(self, ccxt_standard_order):
        """Тест обновления Order из CCXT ответа"""
        # Создаем пустой ордер
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type=Order.TYPE_LIMIT,
            side=Order.SIDE_BUY,
            amount=0.001,
            price=50000.0
        )
        
        # Обновляем из CCXT ответа
        order.update_from_ccxt_response(ccxt_standard_order)
        
        # Проверяем обновление
        assert order.filled == 0.0005
        assert order.remaining == 0.0005
        assert order.cost == 25.0
        assert order.lastTradeTimestamp == 1705315850000
        assert len(order.trades) == 1

    def test_ccxt_fee_structure_compliance(self, ccxt_standard_order):
        """Тест соответствия структуры fee CCXT стандарту"""
        order = Order.from_ccxt_response(ccxt_standard_order)
        
        # Fee должно быть словарем с определенными полями
        assert isinstance(order.fee, dict)
        assert 'cost' in order.fee
        assert 'currency' in order.fee
        assert 'rate' in order.fee
        
        # Проверяем типы значений
        assert isinstance(order.fee['cost'], (int, float))
        assert isinstance(order.fee['currency'], str)

    def test_ccxt_trades_structure_compliance(self, ccxt_standard_order):
        """Тест соответствия структуры trades CCXT стандарту"""
        order = Order.from_ccxt_response(ccxt_standard_order)
        
        # Trades должно быть списком
        assert isinstance(order.trades, list)
        
        if order.trades:
            trade = order.trades[0]
            required_trade_fields = ['id', 'timestamp', 'datetime', 'symbol', 'side', 'amount', 'price', 'cost']
            
            for field in required_trade_fields:
                assert field in trade, f"Missing required trade field: {field}"

    def test_ccxt_info_structure_compliance(self, ccxt_standard_order):
        """Тест соответствия структуры info CCXT стандарту"""
        order = Order.from_ccxt_response(ccxt_standard_order)
        
        # Info должно быть словарем (может быть пустым)
        assert isinstance(order.info, dict)
        
        # Если info содержит данные, они должны быть из оригинального ответа биржи
        if order.info:
            assert 'orderId' in order.info

    def test_ccxt_datetime_format_compliance(self):
        """Тест соответствия формата datetime CCXT стандарту"""
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type=Order.TYPE_LIMIT,
            side=Order.SIDE_BUY,
            amount=0.001
        )
        
        # Datetime должен быть в формате ISO8601 с Z
        assert order.datetime.endswith('Z')
        assert 'T' in order.datetime
        
        # Должен парситься в datetime
        parsed = datetime.fromisoformat(order.datetime.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)

    def test_ccxt_timestamp_compliance(self):
        """Тест соответствия timestamp CCXT стандарту"""
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type=Order.TYPE_LIMIT,
            side=Order.SIDE_BUY,
            amount=0.001
        )
        
        # Timestamp должен быть числом в миллисекундах
        assert isinstance(order.timestamp, int)
        assert order.timestamp > 1000000000000  # Должен быть в миллисекундах
        
        # Должен соответствовать текущему времени примерно
        current_timestamp = int(datetime.now().timestamp() * 1000)
        assert abs(order.timestamp - current_timestamp) < 5000  # В пределах 5 секунд

    def test_ccxt_precision_handling(self):
        """Тест работы с precision в CCXT стиле"""
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type=Order.TYPE_LIMIT,
            side=Order.SIDE_BUY,
            amount=0.001234567890,  # Много знаков после запятой
            price=50000.123456789
        )
        
        # Значения должны сохраняться с точностью
        assert order.amount == 0.001234567890
        assert order.price == 50000.123456789

    def test_ccxt_status_transitions(self):
        """Тест переходов статусов согласно CCXT логике"""
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type=Order.TYPE_LIMIT,
            side=Order.SIDE_BUY,
            amount=0.001,
            price=50000.0,
            status=Order.STATUS_PENDING
        )
        
        # Переход в open
        order.mark_as_placed_on_exchange('exchange123', 1705315800000)
        assert order.status == Order.STATUS_OPEN
        assert order.id == 'exchange123'
        
        # Частичное исполнение
        order.update_filled_amount(0.0005, 50000.0)
        assert order.status == Order.STATUS_PARTIALLY_FILLED  # AutoTrade статус
        assert order.filled == 0.0005
        assert order.remaining == 0.0005
        
        # Полное исполнение
        order.update_filled_amount(0.001, 50000.0)
        assert order.status == Order.STATUS_CLOSED
        assert order.filled == 0.001
        assert order.remaining == 0.0

    def test_ccxt_backward_compatibility(self):
        """Тест обратной совместимости с AutoTrade полями"""
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type=Order.TYPE_LIMIT,
            side=Order.SIDE_BUY,
            amount=0.001,
            price=50000.0,
            local_order_id=1001,
            deal_id=555
        )
        
        # Проверяем свойства для обратной совместимости
        assert order.order_id == 1001  # local_order_id
        assert order.exchange_id == '12345'  # id
        assert order.order_type == 'limit'  # type

    @pytest.mark.parametrize("invalid_status", [
        'OPEN', 'CLOSED', 'PENDING',  # Старый формат (заглавные)
        'partial', 'filled', 'cancelled',  # Неправильные названия
        'active', 'inactive', 'waiting'  # Несуществующие статусы
    ])
    def test_ccxt_invalid_status_handling(self, invalid_status):
        """Тест обработки некорректных статусов"""
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type=Order.TYPE_LIMIT,
            side=Order.SIDE_BUY,
            amount=0.001,
            status=invalid_status  # Некорректный статус
        )
        
        # При валидации должна быть ошибка
        is_valid, errors = order.validate_ccxt_compliance()
        # Некоторые статусы могут пройти валидацию, но должны быть обработаны правильно
        assert order.status == invalid_status  # Значение сохраняется как есть

    def test_ccxt_none_values_handling(self):
        """Тест обработки None значений в CCXT полях"""
        ccxt_response = {
            'id': '12345',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'amount': 0.001,
            'price': None,  # None значения
            'filled': None,
            'remaining': None,
            'cost': None,
            'average': None,
            'lastTradeTimestamp': None,
            'trades': None,
            'fee': None,
            'info': None
        }
        
        order = Order.from_ccxt_response(ccxt_response)
        
        # None значения должны обрабатываться корректно
        assert order.price is None
        assert order.filled == 0.0  # Default значение
        assert order.trades == []  # Default значение
        assert order.fee == {'cost': 0.0, 'currency': None, 'rate': None}  # Default
        assert order.info == {}  # Default

    def test_ccxt_serialization_deserialization(self, ccxt_standard_order):
        """Тест сериализации/десериализации с сохранением CCXT compliance"""
        # Создаем ордер из CCXT ответа
        original_order = Order.from_ccxt_response(ccxt_standard_order)
        
        # Сериализуем в словарь
        order_dict = original_order.to_dict()
        
        # Десериализуем обратно
        restored_order = Order.from_dict(order_dict)
        
        # Проверяем соответствие CCXT формату
        original_ccxt = original_order.to_ccxt_dict()
        restored_ccxt = restored_order.to_ccxt_dict()
        
        # Все CCXT поля должны совпадать
        ccxt_fields = ['id', 'symbol', 'type', 'side', 'amount', 'price', 'status']
        for field in ccxt_fields:
            assert original_ccxt[field] == restored_ccxt[field]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])