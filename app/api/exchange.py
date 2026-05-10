from fastapi import APIRouter, File, UploadFile, Query, HTTPException

from app.deps import SessionDep
from app.services.csv_parser import read_csv_file
from app.services.exchange_service import process_exchange
from app.core.errors import TargetOneCError


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