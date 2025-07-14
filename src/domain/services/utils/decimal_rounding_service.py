
from decimal import Decimal, ROUND_DOWN, ROUND_UP, ROUND_HALF_UP

class DecimalRoundingService:
    """
    Сервис для точных математических операций с использованием Decimal.
    Обеспечивает правильное банковское округление в соответствии с 
    требованиями биржи (precision).
    """

    @staticmethod
    def to_decimal(number) -> Decimal:
        """Преобразует число в Decimal с высокой точностью."""
        # Устанавливаем достаточную точность для большинства криптовалютных операций
        return Decimal(str(number))

    @staticmethod
    def round_to_precision(number, precision: int) -> Decimal:
        """
        Округляет число до заданной точности (количества знаков после запятой).
        Использует стандартное банковское округление (ROUND_HALF_UP).

        Args:
            number: Число для округления (может быть float, str, int).
            precision: Количество знаков после запятой.

        Returns:
            Округленное число в формате Decimal.
        """
        number = DecimalRoundingService.to_decimal(number)
        # Формируем квантификатор, например, '0.0001' для precision=4
        quantizer = Decimal('1e-' + str(precision))
        return number.quantize(quantizer, rounding=ROUND_HALF_UP)

    @staticmethod
    def floor_to_precision(number, precision: int) -> Decimal:
        """
        Округляет число ВНИЗ до заданной точности.
        Это необходимо для количества актива (amount), чтобы не превысить лимиты.
        """
        number = DecimalRoundingService.to_decimal(number)
        quantizer = Decimal('1e-' + str(precision))
        return number.quantize(quantizer, rounding=ROUND_DOWN)

    @staticmethod
    def ceil_to_precision(number, precision: int) -> Decimal:
        """
        Округляет число ВВЕРХ до заданной точности.
        Может быть полезно для расчета цены продажи, чтобы гарантировать прибыль.
        """
        number = DecimalRoundingService.to_decimal(number)
        quantizer = Decimal('1e-' + str(precision))
        return number.quantize(quantizer, rounding=ROUND_UP)
