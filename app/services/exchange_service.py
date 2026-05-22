import csv
import io
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CsvValidationError, TargetOneCError
from app.db.exchange import ExchangeOperation, ExchangeFileRow
from app.services.csv_parser import validate_required_columns
from app.services.onec_client import send_to_1c

from app.validators.item import (
    REQUIRED_COLUMNS as ITEM_COLUMNS,
    validate_item,
)
from app.validators.partners import (
    REQUIRED_COLUMNS as PARTNER_COLUMNS,
    validate_partner,
)
from app.validators.sales import (
    REQUIRED_COLUMNS as SALES_COLUMNS,
    validate_sale,
)


SOURCE_ENTITIES = {"items", "partners", "sales"}

DASHBOARD_ENTITY_BY_SOURCE = {
    "sales": "dashbordsale",
    "items": "dashborditems",
    "partners": "dashbordpartners",
}

DASHBOARD_ENTITIES = set(DASHBOARD_ENTITY_BY_SOURCE.values())

VALID_TARGETS = {"unf", "bp"}


VALIDATORS = {
    "items": {
        "required_columns": ITEM_COLUMNS,
        "validator": validate_item,
    },
    "partners": {
        "required_columns": PARTNER_COLUMNS,
        "validator": validate_partner,
    },
    "sales": {
        "required_columns": SALES_COLUMNS,
        "validator": validate_sale,
    },
}


def build_dashboard_csv_bytes(
    valid_rows_count: int,
    invalid_rows_count: int,
    errors: list[str],
) -> bytes:
    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=[
            "ВерныеСтроки",
            "НеверныеСтроки",
            "Ошибки",
        ],
        delimiter=",",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    writer.writeheader()
    writer.writerow(
        {
            "ВерныеСтроки": valid_rows_count,
            "НеверныеСтроки": invalid_rows_count,
            "Ошибки": ";".join(errors),
        }
    )

    return output.getvalue().encode("utf-8-sig")


def build_dashboard_errors(invalid_rows: list[dict]) -> list[str]:
    errors = []

    for error in invalid_rows:
        row = error.get("row")
        field = error.get("field")
        value = error.get("value")
        message = error.get("message")

        errors.append(
            f"Строка {row}: {field}={value}({message})"
        )

    return errors


async def send_dashboard_to_1c(
    target: str,
    source_entity: str,
    valid_rows_count: int,
    invalid_rows_count: int,
    errors: list[str],
) -> dict:
    dashboard_entity = DASHBOARD_ENTITY_BY_SOURCE[source_entity]

    dashboard_file_content = build_dashboard_csv_bytes(
        valid_rows_count=valid_rows_count,
        invalid_rows_count=invalid_rows_count,
        errors=errors,
    )

    return await send_to_1c(
        target=target,
        entity=dashboard_entity,
        file_content=dashboard_file_content,
        filename=f"{dashboard_entity}.csv",
    )


async def process_exchange(
    session: AsyncSession,
    entity: str,
    target: str,
    filename: str | None,
    rows: list[dict],
    file_content: bytes,
) -> dict:
    if target not in VALID_TARGETS:
        raise ValueError("Unknown target. Use: unf or bp")

    filename = filename or f"{entity}.csv"

    # Если напрямую отправляют dashboard-файл
    if entity in DASHBOARD_ENTITIES:
        result = await send_to_1c(
            target=target,
            entity=entity,
            file_content=file_content,
            filename=filename,
        )

        return {
            "status": "ok",
            "target": target,
            "entity": entity,
            "filename": filename,
            "rows": len(rows),
            "onec_response": result,
        }

    if entity not in SOURCE_ENTITIES:
        allowed = sorted(SOURCE_ENTITIES | DASHBOARD_ENTITIES)
        raise ValueError(
            f"Unknown entity: {entity}. Use: {', '.join(allowed)}"
        )

    config = VALIDATORS[entity]

    validate_required_columns(
        rows=rows,
        required_columns=config["required_columns"],
    )

    operation = ExchangeOperation(
        entity=entity,
        target=target,
        filename=filename,
        status="received",
        total_rows=len(rows),
    )

    session.add(operation)
    await session.flush()

    validated_rows = []
    invalid_rows = []

    for row_info in rows:
        row_number = row_info["row_number"]
        raw_data = row_info["data"]

        try:
            validated_data = config["validator"](raw_data, row_number)

            validated_rows.append(validated_data)

            session.add(
                ExchangeFileRow(
                    operation_id=operation.id,
                    row_number=row_number,
                    status="valid",
                    raw_data=raw_data,
                    validated_data=validated_data,
                )
            )

        except CsvValidationError as exc:
            invalid_rows.append(
                {
                    "row": exc.row_number,
                    "field": exc.field,
                    "value": exc.value,
                    "message": exc.message,
                }
            )

            session.add(
                ExchangeFileRow(
                    operation_id=operation.id,
                    row_number=row_number,
                    status="invalid",
                    raw_data=raw_data,
                    validated_data=None,
                    error_message=exc.message,
                )
            )

    operation.valid_rows = len(validated_rows)
    operation.invalid_rows = len(invalid_rows)

    # Если есть ошибки — основной файл НЕ отправляем,
    # но отчёт в dashboard отправляем.
    if invalid_rows:
        dashboard_errors = build_dashboard_errors(invalid_rows)

        try:
            dashboard_response = await send_dashboard_to_1c(
                target=target,
                source_entity=entity,
                valid_rows_count=len(validated_rows),
                invalid_rows_count=len(invalid_rows),
                errors=dashboard_errors,
            )
        except TargetOneCError as exc:
            dashboard_response = {
                "status": "error",
                "message": exc.message,
                "status_code": exc.status_code,
                "response_text": exc.response_text,
            }

        operation.status = "validation_failed"
        operation.error_message = "CSV contains invalid rows"
        operation.finished_at = datetime.utcnow()

        await session.commit()

        return {
            "status": "error",
            "operation_id": operation.id,
            "error": {
                "code": "CSV_VALIDATION_ERROR",
                "message": "CSV contains invalid rows",
                "details": {
                    "errors": invalid_rows,
                },
            },
            "statistics": {
                "total_rows": operation.total_rows,
                "valid_rows": operation.valid_rows,
                "invalid_rows": operation.invalid_rows,
                "sent_rows": operation.sent_rows or 0,
            },
            "dashboard": {
                "entity": DASHBOARD_ENTITY_BY_SOURCE[entity],
                "response": dashboard_response,
            },
        }

    operation.status = "sending"
    await session.commit()

    try:
        # Основной CSV отправляем в 1С как есть
        result = await send_to_1c(
            target=target,
            entity=entity,
            file_content=file_content,
            filename=filename,
        )

        # После успешной отправки основного файла отправляем dashboard
        dashboard_response = await send_dashboard_to_1c(
            target=target,
            source_entity=entity,
            valid_rows_count=len(validated_rows),
            invalid_rows_count=0,
            errors=[],
        )

    except TargetOneCError as exc:
        operation.status = "failed"
        operation.error_message = exc.message
        operation.target_status_code = exc.status_code
        operation.target_response = exc.response_text
        operation.finished_at = datetime.utcnow()

        await session.commit()

        return {
            "status": "error",
            "operation_id": operation.id,
            "error": {
                "code": "TARGET_1C_ERROR",
                "message": exc.message,
                "details": {
                    "target": target,
                    "entity": entity,
                    "target_status_code": exc.status_code,
                    "target_response": exc.response_text,
                },
            },
            "statistics": {
                "total_rows": operation.total_rows,
                "valid_rows": operation.valid_rows,
                "invalid_rows": operation.invalid_rows,
                "sent_rows": operation.sent_rows or 0,
            },
        }

    operation.status = "success"
    operation.sent_rows = len(validated_rows)
    operation.target_status_code = result["status_code"]
    operation.target_response = result["text"]
    operation.finished_at = datetime.utcnow()

    await session.commit()

    return {
        "status": "ok",
        "operation_id": operation.id,
        "message": "File processed and sent to target 1C",
        "target": target,
        "entity": entity,
        "filename": filename,
        "statistics": {
            "total_rows": operation.total_rows,
            "valid_rows": operation.valid_rows,
            "invalid_rows": operation.invalid_rows,
            "sent_rows": operation.sent_rows,
        },
        "target_response": result["json"] or result["text"],
        "dashboard": {
            "entity": DASHBOARD_ENTITY_BY_SOURCE[entity],
            "response": dashboard_response,
        },
    }