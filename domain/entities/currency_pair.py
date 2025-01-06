# my_trading_app/domain/entities/currency_pair.py

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
        profit_markup: float = 0.002,
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

    def __repr__(self):
        return (f"<CurrencyPair(symbol={self.symbol}, "
                f"order_life_time={self.order_life_time}, "
                f"deal_quota={self.deal_quota})>")
