from datetime import date
from decimal import Decimal, InvalidOperation


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def parse_date(value, field):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ApiError(f"Format {field} tidak valid (YYYY-MM-DD).")


def parse_amount(value, field="nominal"):
    if value in (None, ""):
        return None
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise ApiError(f"{field.capitalize()} harus berupa angka.")
    if amount <= 0:
        raise ApiError(f"{field.capitalize()} harus lebih dari 0.")
    return amount.quantize(Decimal("0.01"))
