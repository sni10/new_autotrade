# my_trading_app/domain/entities/currency_pair.py
import logging

class CurrencyPair:
    """
    Упрощённая сущность 'Валютная пара'.
    """

    def __init__(
        self,
        base_currency: str,
        quote_currency: str,
        symbol: str = None,
        order_life_time: int = 1,
        deal_quota: float = 100.0,
        # """
        # profit_markup = 0.5%.
        # """
        profit_markup: float = 0.005,
        deal_count: int = 1
    ):
        """
        symbol, например "BTC/USDT"
        order_life_time - сколько минут живёт ордер до отмены
        deal_quota - размер сделки в quote
        profit_markup - желаемый профит (0.002 = 0.2%)
        deal_count - сколько одновременно может быть открыто сделок
        """
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.symbol = symbol or f"{base_currency}/{quote_currency}"
        self.order_life_time = order_life_time
        self.deal_quota = deal_quota
        self.profit_markup = profit_markup
        self.deal_count = deal_count
        self.precision = {}
        self.limits = {}
        self.taker_fee = 0.001  # Default taker fee
        self.maker_fee = 0.001  # Default maker fee

    def update_exchange_info(self, market_data):
        """
        Обновляет точность, лимиты и комиссии из данных, полученных с биржи.
        """
        if not market_data:
            return
        
        # Если это ExchangeInfo объект
        if hasattr(market_data, 'precision'):
            self.precision = market_data.precision
            self.limits = {
                'amount': {'min': market_data.min_qty, 'max': market_data.max_qty},
                'price': {'min': market_data.min_price, 'max': market_data.max_price},
                'cost': {'min': market_data.min_notional}
            }
            self.taker_fee = market_data.fees.get('taker', self.taker_fee)
            self.maker_fee = market_data.fees.get('maker', self.maker_fee)
        # Если это словарь (legacy)
        else:
            self.precision = market_data.get('precision', {})
            self.limits = market_data.get('limits', {})
            self.taker_fee = market_data.get('taker', self.taker_fee)
            self.maker_fee = market_data.get('maker', self.maker_fee)
            
        logging.info(f"Updated currency pair {self.symbol} with exchange data: Precision={self.precision}, Limits={self.limits}, Fees(T/M)={self.taker_fee}/{self.maker_fee}")

    def __repr__(self):
        return (f"<CurrencyPair(symbol={self.symbol}, "
                f"order_life_time={self.order_life_time}, "
                )
