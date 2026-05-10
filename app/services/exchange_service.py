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


VALIDATORS = {
    "items": {
        "required_columns": ITEM_COLUMNS,
        "validator": validate_item,
        "payload_key": "items",
    },
    "partners": {
        "required_columns": PARTNER_COLUMNS,
        "validator": validate_partner,
        "payload_key": "partners",
    },
    "sales": {
        "required_columns": SALES_COLUMNS,
        "validator": validate_sale,
        "payload_key": "sales",
    },
}


async def process_exchange(
    session: AsyncSession,
    entity: str,
    target: str,
    filename: str | None,
    rows: list[dict],
) -> dict:
    if entity not in VALIDATORS:
        raise ValueError("Unknown entity. Use: items, partners, sales")

    if target not in {"unf", "bp"}:
        raise ValueError("Unknown target. Use: unf or bp")

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
            invalid_rows.append({
                "row": exc.row_number,
                "field": exc.field,
                "value": exc.value,
                "message": exc.message,
            })

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

    if invalid_rows:
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
                "sent_rows": operation.sent_rows,
            },
        }

    operation.status = "sending"
    await session.commit()

    payload_key = config["payload_key"]

    payload = {
        "source": "fastapi",
        "target": target,
        "entity": entity,
        payload_key: validated_rows,
    }

    try:
        result = await send_to_1c(
            target=target,
            entity=entity,
            payload=payload,
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
                "sent_rows": operation.sent_rows,
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
        "statistics": {
            "total_rows": operation.total_rows,
            "valid_rows": operation.valid_rows,
            "invalid_rows": operation.invalid_rows,
            "sent_rows": operation.sent_rows,
        },
        "target_response": result["json"] or result["text"],
    }

from app.services.onec_client import send_to_1c


VALID_ENTITIES = {"items", "partners", "sales"}
VALID_TARGETS = {"unf", "bp"}


async def process_exchange(
    session,
    entity: str,
    target: str,
    filename: str,
    rows: list[dict],
    file_content: bytes,
) -> dict:
    if entity not in VALID_ENTITIES:
        raise ValueError(f"Unknown entity: {entity}")

    if target not in VALID_TARGETS:
        raise ValueError(f"Unknown target: {target}")

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