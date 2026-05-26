"""Sample pytest tests demonstrating common patterns."""
import pytest


def calculate_tax(amount: float, rate: float = 0.1) -> float:
    if amount < 0:
        raise ValueError("amount must be non-negative")
    return round(amount * rate, 2)


def test_calculate_tax_basic():
    assert calculate_tax(100) == 10.0


@pytest.mark.parametrize("amount,rate,expected", [(100, 0.1, 10.0), (200, 0.2, 40.0), (0, 0.1, 0.0)])
def test_calculate_tax_parametrized(amount, rate, expected):
    assert calculate_tax(amount, rate) == expected


def test_calculate_tax_invalid():
    with pytest.raises(ValueError):
        calculate_tax(-1)


@pytest.fixture
def sample_rows():
    return [{"id": 1, "amount": 100}, {"id": 2, "amount": 200}]


def test_total(sample_rows):
    assert sum(row["amount"] for row in sample_rows) == 300
