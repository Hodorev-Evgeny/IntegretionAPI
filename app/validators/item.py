from app.core.errors import CsvValidationError
from app.validators.common import get_optional, get_required_any, parse_optional_int


REQUIRED_COLUMNS = {
    "Наименование",
    "ЕдиницыИзмерения",
}


def validate_item(row: dict, row_number: int) -> dict:
    name = get_required_any(
        row,
        ["Наименование", "name"],
        row_number,
    )

    uom = get_required_any(
        row,
        ["ЕдиницыИзмерения", "uom"],
        row_number,
    )

    if uom not in {"л", "шт"}:
        raise CsvValidationError(
            row_number=row_number,
            field="ЕдиницыИзмерения",
            value=uom,
            message='ЕдиницыИзмерения должны быть только "л" или "шт"',
        )

    vat_raw = (
        get_optional(row, "НДС")
        or get_optional(row, "vat_rate")
    )

    vat_rate = parse_optional_int(vat_raw, "НДС", row_number)

    code = (
        get_optional(row, "Код")
        or get_optional(row, "code")
        or name
    )

    return {
        "code": code,
        "name": name,
        "uom": uom,
        "vat_rate": vat_rate,
    }