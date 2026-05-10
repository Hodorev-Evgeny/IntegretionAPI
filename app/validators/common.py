from decimal import Decimal, InvalidOperation

from app.core.errors import CsvValidationError


def get_value(row: dict, *fields: str):
    for field in fields:
        if field in row:
            return row.get(field)
    return None


def get_required(row: dict, field: str, row_number: int) -> str:
    value = row.get(field)

    if value is None or str(value).strip() == "":
        raise CsvValidationError(
            row_number=row_number,
            field=field,
            value=value,
            message=f"Поле '{field}' обязательно для заполнения",
        )

    return str(value).strip()


def get_required_any(row: dict, fields: list[str], row_number: int) -> str:
    for field in fields:
        value = row.get(field)
        if value is not None and str(value).strip() != "":
            return str(value).strip()

    raise CsvValidationError(
        row_number=row_number,
        field="/".join(fields),
        value=None,
        message=f"Одно из полей обязательно для заполнения: {', '.join(fields)}",
    )


def get_optional(row: dict, field: str) -> str | None:
    value = row.get(field)

    if value is None or str(value).strip() == "":
        return None

    return str(value).strip()


def parse_optional_int(value, field: str, row_number: int) -> int | None:
    if value is None or str(value).strip() == "":
        return None

    try:
        return int(str(value).strip())
    except ValueError:
        raise CsvValidationError(
            row_number=row_number,
            field=field,
            value=value,
            message=f"Поле '{field}' должно быть числом",
        )


def parse_decimal(value, field: str, row_number: int) -> Decimal:
    if value is None or str(value).strip() == "":
        raise CsvValidationError(
            row_number=row_number,
            field=field,
            value=value,
            message=f"Поле '{field}' обязательно для заполнения",
        )

    value = str(value).replace(",", ".").strip()

    try:
        result = Decimal(value)
    except InvalidOperation:
        raise CsvValidationError(
            row_number=row_number,
            field=field,
            value=value,
            message=f"Поле '{field}' должно быть числом",
        )

    if result <= 0:
        raise CsvValidationError(
            row_number=row_number,
            field=field,
            value=value,
            message=f"Поле '{field}' должно быть больше 0",
        )

    return result