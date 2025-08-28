
import sys
import os
from decimal import Decimal
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))

from domain.services.utils.decimal_rounding_service import DecimalRoundingService

@pytest.mark.parametrize("number, precision, expected", [
    (123.456, 2, Decimal('123.46')),
    (123.454, 2, Decimal('123.45')),
    ('123.456', 0, Decimal('123')),
    (123, 2, Decimal('123.00')),
])
def test_round_to_precision(number, precision, expected):
    assert DecimalRoundingService.round_to_precision(number, precision) == expected

@pytest.mark.parametrize("number, precision, expected", [
    (123.456, 2, Decimal('123.45')),
    (123.459, 2, Decimal('123.45')),
    ('123.9', 0, Decimal('123')),
])
def test_floor_to_precision(number, precision, expected):
    assert DecimalRoundingService.floor_to_precision(number, precision) == expected

@pytest.mark.parametrize("number, precision, expected", [
    (123.451, 2, Decimal('123.46')),
    (123.450, 2, Decimal('123.45')),
    ('123.1', 0, Decimal('124')),
])
def test_ceil_to_precision(number, precision, expected):
    assert DecimalRoundingService.ceil_to_precision(number, precision) == expected
