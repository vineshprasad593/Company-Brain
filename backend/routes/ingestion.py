import pandas as pd
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import text

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


from database.connection import engine

# Approved business tables for CSV ingestion.
# Never accept arbitrary table names from upload requests.
ALLOWED_INGESTION_TABLES = {
    "business_rules",
    "company_master",
    "customers",
    "documents",
    "emails",
    "employees",
    "events",
    "expenses",
    "payments",
    "purchase_orders",
    "sales_invoices",
    "sales_orders",
    "shipments",
    "vendor_invoices",
    "vendors",
    "ingestion_test_business_rules",
}


router = APIRouter(
    prefix="/api/v1/ingestion",
    tags=["Data Ingestion"]
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/csv/preview")
async def preview_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported by this endpoint."
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum size is 10 MB."
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV file is empty."
        )

    try:
        df = pd.read_csv(BytesIO(contents))
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError):
        raise HTTPException(
            status_code=400,
            detail="Could not read this CSV. Check its encoding and format."
        )

    if len(df.columns) == 0:
        raise HTTPException(
            status_code=400,
            detail="The CSV must contain column headers."
        )

    preview = df.head(5).astype(object).where(
        pd.notna(df.head(5)), None
    )

    return {
        "filename": file.filename,
        "rows_detected": len(df),
        "columns": df.columns.tolist(),
        "preview": preview.to_dict(orient="records"),
        "database_inserted": False
    }


@router.post("/csv/test-insert")
async def test_insert_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported."
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 10 MB limit."
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV file is empty."
        )

    try:
        df = pd.read_csv(BytesIO(contents))
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError):
        raise HTTPException(
            status_code=400,
            detail="Could not read the CSV file."
        )

    required_columns = [
        "rule_id", "rule_name", "rule_text", "department"
    ]

    if not all(column in df.columns for column in required_columns):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain these columns: {required_columns}"
        )

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="The CSV contains no data rows."
        )

    if df[required_columns].isna().any().any():
        raise HTTPException(
            status_code=400,
            detail="Required fields cannot be empty."
        )

    if df["rule_id"].duplicated().any():
        raise HTTPException(
            status_code=400,
            detail="Duplicate rule_id values found."
        )

    records = df[required_columns].to_dict(orient="records")

    try:
        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO ingestion_test_business_rules
                    (rule_id, rule_name, rule_text, department)
                    VALUES
                    (:rule_id, :rule_name, :rule_text, :department)
                """),
                records
            )
    except Exception as exc:
        
        if "IntegrityError" in type(exc).__name__:
            raise HTTPException(
                status_code=409,
                detail="A rule_id already exists in the test table."
            )

        raise HTTPException(
            status_code=500,
            detail="The CSV could not be inserted into the test table."
        )

    return {
        "message": "CSV inserted successfully into the test table.",
        "filename": file.filename,
        "rows_inserted": len(records),
        "destination_table": "ingestion_test_business_rules"
    }


@router.post("/csv/ingest")
async def ingest_csv(
    table_name: str,
    file: UploadFile = File(...)
):
    # Only approved business tables are allowed.
    if table_name not in ALLOWED_INGESTION_TABLES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported destination table."
        )

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported."
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 10 MB limit."
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV file is empty."
        )

    try:
        df = pd.read_csv(BytesIO(contents))
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError):
        raise HTTPException(
            status_code=400,
            detail="Could not read the CSV file."
        )

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="The CSV contains no data rows."
        )

    if not df.columns.is_unique:
        raise HTTPException(
            status_code=400,
            detail="Duplicate column names are not allowed."
        )

    if any(not isinstance(col, str) or not col.strip() for col in df.columns):
        raise HTTPException(
            status_code=400,
            detail="Every CSV column must have a valid header."
        )

    # Fetch the destination table's actual columns from PostgreSQL.
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT column_name, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = :table_name
                    ORDER BY ordinal_position
                """),
                {"table_name": table_name}
            )
            schema_rows = result.mappings().all()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not inspect the destination table."
        )

    if not schema_rows:
        raise HTTPException(
            status_code=400,
            detail="Destination table does not exist."
        )

    schema_columns = {row["column_name"] for row in schema_rows}
    csv_columns = set(df.columns)

    unknown_columns = csv_columns - schema_columns
    if unknown_columns:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV contains columns not present in the destination table.",
                "unknown_columns": sorted(unknown_columns)
            }
        )

    missing_required = {
        row["column_name"]
        for row in schema_rows
        if row["is_nullable"] == "NO"
        and row["column_default"] is None
        and row["column_name"] not in csv_columns
    }

    if missing_required:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV is missing required columns.",
                "missing_columns": sorted(missing_required)
            }
        )

   
    # Convert pandas NaN values to Python None for SQL NULL.
    df = df.astype(object).where(pd.notna(df), None)

    # Identify columns that require values in PostgreSQL.
    required_columns = {
        row["column_name"]
        for row in schema_rows
        if row["is_nullable"] == "NO"
        and row["column_default"] is None
    }

    # Reject empty or whitespace-only values in required columns.
    empty_required = []

    for column in required_columns:
        if column not in df.columns:
            continue

        for index, value in df[column].items():
            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                empty_required.append({
                    "row": int(index) + 2,
                    "column": column
                })

    if empty_required:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV contains empty values in required columns.",
                "invalid_fields": empty_required
            }
        )

    records = df.to_dict(orient="records")


    try:
        with engine.begin() as connection:
            # Check for duplicate values within the upload on primary keys.
            pk_result = connection.execute(
                text("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                     AND tc.table_name = kcu.table_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                      AND tc.table_schema = 'public'
                      AND tc.table_name = :table_name
                    ORDER BY kcu.ordinal_position
                """),
                {"table_name": table_name}
            )
            primary_keys = [row[0] for row in pk_result]

            for column in primary_keys:
                values = [record.get(column) for record in records]
                non_null_values = [value for value in values if value is not None]

                if len(non_null_values) != len(set(non_null_values)):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate primary-key values in column '{column}'."
                    )

            # Table and column identifiers come only from validated schema names.
            columns_sql = ", ".join(f'"{column}"' for column in df.columns)
            placeholders = ", ".join(f":{column}" for column in df.columns)

            insert_sql = text(
                f'INSERT INTO public."{table_name}" ({columns_sql}) '
                f'VALUES ({placeholders})'
            )

            connection.execute(insert_sql, records)

    
    except HTTPException:
        raise
    except IntegrityError as exc:
        print("CSV ingestion constraint error:", repr(exc))
        raise HTTPException(
            status_code=409,
            detail=(
                "Insertion failed because of a database constraint, "
                "such as a duplicate key or invalid relationship."
            )
        )
    except Exception as exc:
        print("CSV ingestion error:", repr(exc))
        raise HTTPException(
            status_code=400,
            detail=(
                "CSV insertion failed. Check the data types "
                "and database constraints."
            )
        )
