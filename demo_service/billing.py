from decimal import Decimal, ROUND_HALF_UP


def calculate_total(unit_price: str, quantity: int) -> str:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    total = Decimal(unit_price) * quantity
    return format(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")
