# tests/domain/entities/test_order_entity.py
import unittest
import time
from src.domain.entities.order import Order

class TestOrderEntity(unittest.TestCase):

    def setUp(self):
        """Настройка тестового словаря, имитирующего ответ от ccxt."""
        self.ccxt_order_data = {
            'id': 'EXCH-12345',  # Используем 'id' как в ccxt
            'symbol': 'BTC/USDT',
            'type': 'limit',  # Используем 'type' как в ccxt
            'side': 'buy',
            'price': 50000.0,
            'amount': 1.5,
            'status': 'open',
            'timestamp': int(time.time() * 1000) - 5000,
            'datetime': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime((time.time() * 1000 - 5000)/1000)),
            'filled': 0.5,
            'remaining': 1.0,
            'average': 50005.0,
            'cost': 25002.5,
            'fee': {'cost': 5.0, 'currency': 'USDT'},
            'trades': [{'id': 'trade-1', 'price': 50005.0, 'amount': 0.5}],
            'info': {'binance-specific-field': 'some-value'},
            # Добавляем наши внутренние поля, которые могут быть в сохраненных данных
            'deal_id': 789,
            'order_id': 123, # Наше внутреннее ID, может отличаться от exchange_id
            'retries': 1,
            'metadata': {'source': 'test'},
        }

    def test_creation_from_ccxt_dict(self):
        """Тест: Сущность Order корректно создается из ccxt-подобного словаря."""
        order = Order.from_dict(self.ccxt_order_data)
        
        self.assertIsInstance(order, Order)
        self.assertEqual(order.order_id, self.ccxt_order_data['order_id'])
        self.assertEqual(order.exchange_id, self.ccxt_order_data['id'])
        self.assertEqual(order.order_type, self.ccxt_order_data['type'])
        self.assertEqual(order.filled_amount, self.ccxt_order_data['filled'])
        self.assertEqual(order.average_price, self.ccxt_order_data['average'])
        self.assertEqual(order.fees, self.ccxt_order_data['fee']['cost'])
        self.assertDictEqual(order.exchange_raw_data, self.ccxt_order_data['info'])
        self.assertEqual(order.deal_id, self.ccxt_order_data['deal_id'])

    def test_serialization_to_dict(self):
        """Тест: Метод to_dict() корректно сериализует все поля сущности."""
        order = Order.from_dict(self.ccxt_order_data)
        serialized_data = order.to_dict()
        
        # Проверяем, что ключевые поля были правильно перенесены и сериализованы
        self.assertEqual(serialized_data['order_id'], self.ccxt_order_data['order_id'])
        self.assertEqual(serialized_data['exchange_id'], self.ccxt_order_data['id'])
        self.assertEqual(serialized_data['order_type'], self.ccxt_order_data['type'])
        self.assertEqual(serialized_data['filled_amount'], self.ccxt_order_data['filled'])
        self.assertEqual(serialized_data['average_price'], self.ccxt_order_data['average'])
        self.assertEqual(serialized_data['fees'], self.ccxt_order_data['fee']['cost'])
        self.assertDictEqual(serialized_data['exchange_raw_data'], self.ccxt_order_data['info'])

    def test_update_from_exchange_data(self):
        """Тест: Метод update_from_exchange корректно обновляет поля."""
        order = Order.from_dict(self.ccxt_order_data)
        
        update_data = {
            'id': 'EXCH-12345',
            'filled': 1.0,
            'remaining': 0.5,
            'average': 50010.0,
            'status': 'open',
            'cost': 50010.0,
            'lastTradeTimestamp': int(time.time() * 1000),
            'trades': [
                {'id': 'trade-1', 'price': 50005.0, 'amount': 0.5},
                {'id': 'trade-2', 'price': 50015.0, 'amount': 0.5}
            ],
            'fee': {'cost': 7.5, 'currency': 'USDT'}
        }
        
        order.update_from_exchange(update_data)
        
        self.assertEqual(order.filled_amount, 1.0)
        self.assertEqual(order.remaining_amount, 0.5)
        self.assertEqual(order.average_price, 50010.0)
        self.assertEqual(order.cost, 50010.0)
        self.assertEqual(order.fees, 7.5)
        self.assertEqual(len(order.trades), 2)
        self.assertTrue(order.is_partially_filled())

if __name__ == '__main__':
    unittest.main()
