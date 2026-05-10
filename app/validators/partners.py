from app.core.errors import CsvValidationError
from app.validators.common import get_optional, get_required_any


REQUIRED_COLUMNS = {
    "Наименование",
}


def validate_partner(row: dict, row_number: int) -> dict:
    name = get_required_any(
        row,
        ["Наименование", "name"],
        row_number,
    )

    inn = (
        get_optional(row, "ИНН")
        or get_optional(row, "inn")
    )

    kpp = (
        get_optional(row, "КПП")
        or get_optional(row, "kpp")
    )

    if inn is not None and (not inn.isdigit() or len(inn) not in {10, 12}):
        raise CsvValidationError(
            row_number=row_number,
            field="ИНН",
            value=inn,
            message="ИНН должен содержать 10 или 12 цифр либо быть пустым",
        )

    if kpp is not None and (not kpp.isdigit() or len(kpp) != 9):
        raise CsvValidationError(
            row_number=row_number,
            field="КПП",
            value=kpp,
            message="КПП должен содержать 9 цифр либо быть пустым",
        )

    return {
        "name": name,
        "inn": inn,
        "kpp": kpp,
    }