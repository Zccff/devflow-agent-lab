from demo_service.auth import login
from demo_service.billing import calculate_total


def checkout(token: str, unit_price: str, quantity: int, now: int) -> dict:
    identity = login(token, now)
    if identity["status"] != 200:
        return identity
    return {
        "status": 200,
        "user": identity["user"],
        "currency": "CNY",
        "total": calculate_total(unit_price, quantity),
    }
