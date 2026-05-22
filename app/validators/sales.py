from datetime import datetime

from app.core.errors import CsvValidationError


REQUIRED_COLUMNS = {
    "НомерДокумента",
    "Дата",
    "КонтрагентИНН",
    "СтрокаТаблицы",
    "НаименованиеКонтрагента",
}


def validate_1c_date(value: str, row_number: int) -> str:
    value = str(value or "").strip()

    if not value:
        raise CsvValidationError(
            row_number=row_number,
            field="Дата",
            value=value,
            message="Дата обязательна",
        )

    if not (len(value) == 14 and value.isdigit()):
        raise CsvValidationError(
            row_number=row_number,
            field="Дата",
            value=value,
            message="Дата должна быть в формате YYYYMMDDHHMMSS",
        )

    try:
        datetime.strptime(value, "%Y%m%d%H%M%S")
    except ValueError:
        raise CsvValidationError(
            row_number=row_number,
            field="Дата",
            value=value,
            message="Некорректная дата",
        )

    return value


def parse_table_rows(value: str, row_number: int) -> list[dict]:
    value = str(value or "").strip()

    # В эталонном файле СтрокаТаблицы может быть пустой.
    # Это не ошибка.
    if not value:
        return []

    result = []

    parts = [
        part.strip()
        for part in value.split(";")
        if part.strip()
    ]

    for part in parts:
        item_parts = [x.strip() for x in part.split("/")]

        if len(item_parts) != 4:
            raise CsvValidationError(
                row_number=row_number,
                field="СтрокаТаблицы",
                value=part,
                message="Товар должен быть в формате Товар/Количество/Цена/Сумма",
            )

        product_name, quantity, price, amount = item_parts

        if not product_name:
            raise CsvValidationError(
                row_number=row_number,
                field="СтрокаТаблицы",
                value=part,
                message="Не указано наименование товара",
            )

        try:
            quantity_value = float(quantity.replace(",", "."))
            price_value = float(price.replace(",", "."))
            amount_value = float(amount.replace(",", "."))
        except ValueError:
            raise CsvValidationError(
                row_number=row_number,
                field="СтрокаТаблицы",
                value=part,
                message="Количество, цена и сумма должны быть числами",
            )

        result.append(
            {
                "Товар": product_name,
                "Количество": quantity_value,
                "Цена": price_value,
                "Сумма": amount_value,
            }
        )

    return result


def validate_sale(row: dict, row_number: int) -> dict:
    document_number = str(row.get("НомерДокумента") or "").strip()
    date = validate_1c_date(row.get("Дата"), row_number)
    counterparty_inn = str(row.get("КонтрагентИНН") or "").strip()
    table_rows_raw = str(row.get("СтрокаТаблицы") or "").strip()
    counterparty_name = str(row.get("НаименованиеКонтрагента") or "").strip()

    if not document_number:
        raise CsvValidationError(
            row_number=row_number,
            field="НомерДокумента",
            value=document_number,
            message="Номер документа обязателен",
        )

    if not counterparty_inn and not counterparty_name:
        raise CsvValidationError(
            row_number=row_number,
            field="КонтрагентИНН",
            value=counterparty_inn,
            message="Нужно указать ИНН или наименование контрагента",
        )

    table_rows = parse_table_rows(table_rows_raw, row_number)

    return {
        "НомерДокумента": document_number,
        "Дата": date,
        "КонтрагентИНН": counterparty_inn,
        "СтрокаТаблицы": table_rows_raw,
        "НаименованиеКонтрагента": counterparty_name,
        "Товары": table_rows,
    }