import csv
import io

from fastapi import UploadFile, HTTPException


async def read_csv_file(file: UploadFile) -> list[dict]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="File must have .csv extension",
        )

    content = await file.read()

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV file must be encoded in UTF-8",
        )

    csvfile = io.StringIO(text)
    reader = csv.DictReader(csvfile)

    if not reader.fieldnames:
        raise HTTPException(
            status_code=400,
            detail="CSV file is empty or has no header",
        )

    rows = []

    for row_number, row in enumerate(reader, start=2):
        rows.append({
            "row_number": row_number,
            "data": row,
        })

    return rows


def validate_required_columns(
    rows: list[dict],
    required_columns: set[str],
):
    if not rows:
        return

    first_row = rows[0]["data"]
    existing_columns = set(first_row.keys())
    missing_columns = required_columns - existing_columns

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing_columns))}",
        )