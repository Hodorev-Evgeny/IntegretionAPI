from datetime import date

from app.core.errors import CsvValidationError
from app.validators.common import get_optional, get_required_any, parse_decimal


REQUIRED_COLUMNS = {
    "НаименованиеКонтрагента",
    "Товар",
    "Количество",
    "Цена",
}


def validate_sale(row: dict, row_number: int) -> dict:
    partner_name = get_required_any(
        row,
        ["НаименованиеКонтрагента", "partner_name"],
        row_number,
    )

    item_name = get_required_any(
        row,
        ["Товар", "Номенклатура", "item_name", "item_code"],
        row_number,
    )

    qty_raw = get_required_any(
        row,
        ["Количество", "qty"],
        row_number,
    )

    price_raw = get_required_any(
        row,
        ["Цена", "price"],
        row_number,
    )

    qty = parse_decimal(qty_raw, "Количество", row_number)
    price = parse_decimal(price_raw, "Цена", row_number)

    doc_no = (
        get_optional(row, "Номер")
        or get_optional(row, "doc_no")
        or f"row-{row_number}"
    )

    sale_date_raw = (
        get_optional(row, "Дата")
        or get_optional(row, "sale_date")
    )

    print(sale_date_raw)

    return {
        "doc_no": doc_no,
        "sale_date": sale_date_raw,
        "partner_name": partner_name,
        "item_name": item_name,
        "qty": str(qty),
        "price": str(price),
    }