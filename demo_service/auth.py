"""Synthetic token format: username:expiry_timestamp. Not production authentication."""


class InvalidTokenError(Exception):
    pass


class ExpiredTokenError(Exception):
    pass


def validate_token(token: str, now: int) -> str:
    try:
        username, expiry = token.rsplit(":", 1)
        expiry_timestamp = int(expiry)
    except (AttributeError, ValueError) as exc:
        raise InvalidTokenError("invalid demo credential") from exc
    if not username:
        raise InvalidTokenError("missing username")
    if expiry_timestamp <= now:
        raise ExpiredTokenError("demo credential has expired")
    return username


def login(token: str, now: int) -> dict:
    try:
        username = validate_token(token, now)
        return {"status": 200, "user": username}
    except InvalidTokenError:
        return {"status": 401, "error": "authentication required"}
    except Exception:
        return {"status": 500, "error": "internal server error"}
