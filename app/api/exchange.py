from fastapi import APIRouter, File, UploadFile, Query, HTTPException
from sqlalchemy import select

from app.deps import SessionDep
from app.services.csv_parser import read_csv_file
from app.services.exchange_service import process_exchange
from app.core.errors import TargetOneCError
from app.db.exchange import ExchangeOperation, ExchangeFileRow

router = APIRouter(
    prefix="/exchange",
    tags=["Exchange"],
)


@router.post("/{entity}")
async def exchange_file(
    entity: str,
    session: SessionDep,
    target: str = Query(..., description="Target 1C: unf or bp"),
    file: UploadFile = File(...),
):
    try:
        file_content = await file.read()
        await file.seek(0)

        rows = await read_csv_file(file)
        print("CSV rows:", rows)

        if rows:
            print("First row date:", rows[0].get("Дата"))

        return await process_exchange(
            session=session,
            entity=entity,
            target=target,
            filename=file.filename or f"{entity}.csv",
            rows=rows,
            file_content=file_content,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except TargetOneCError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": getattr(exc, "message", str(exc)),
                "status_code": getattr(exc, "status_code", None),
                "response_text": getattr(exc, "response_text", None),
            },
        )
    
@router.get("/status/{operation_id}")
async def get_exchange_status(
    operation_id: int,
    session: SessionDep,
):
    operation = await session.get(ExchangeOperation, operation_id)

    if operation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exchange operation {operation_id} not found",
        )

    invalid_rows_result = await session.execute(
        select(ExchangeFileRow)
        .where(ExchangeFileRow.operation_id == operation.id)
        .where(ExchangeFileRow.status == "invalid")
        .order_by(ExchangeFileRow.row_number)
    )

    invalid_rows = invalid_rows_result.scalars().all()

    errors = [
        {
            "row_number": row.row_number,
            "message": row.error_message,
            "raw_data": row.raw_data,
        }
        for row in invalid_rows
    ]

    return {
        "operation_id": operation.id,
        "status": operation.status,
        "target": operation.target,
        "entity": operation.entity,
        "filename": operation.filename,
        "statistics": {
            "total_rows": operation.total_rows,
            "valid_rows": operation.valid_rows,
            "invalid_rows": operation.invalid_rows,
            "sent_rows": operation.sent_rows,
        },
        "target": {
            "status_code": operation.target_status_code,
            "response": operation.target_response,
        },
        "error_message": operation.error_message,
        "errors": errors,
        "created_at": operation.created_at,
        "finished_at": operation.finished_at,
    }