MAX_ORDER_QUANTITY = 5


def reserve_stock(stock: int, quantity: int) -> int:
    if quantity <= 0 or quantity > MAX_ORDER_QUANTITY:
        raise ValueError("quantity must be between 1 and 5")
    if stock < quantity:
        raise ValueError("insufficient stock")
    return stock - quantity
