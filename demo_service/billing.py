"""Legacy float implementation. The rounding PR supplies the intended Decimal fix."""


def calculate_total(unit_price: str, quantity: int) -> str:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    return f"{float(unit_price) * quantity:.2f}"
