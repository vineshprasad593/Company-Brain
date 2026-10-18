
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database.connection import engine


DATA_DIR = Path(__file__).resolve().parents[2] / "data"

IMPORT_ORDER = [
    "employees",
    "vendors",
    "customers",
    "company_master",
    "business_rules",
    "sales_orders",
    "purchase_orders",
    "sales_invoices",
    "payments",
    "shipments",
    "vendor_invoices",
    "expenses",
    "documents",
    "emails",
    "events",
]

DATE_COLUMNS = {
    "employees": ["joining_date"],
    "sales_orders": ["order_date"],
    "sales_invoices": ["invoice_date"],
    "payments": ["payment_date"],
    "shipments": [
        "pickup_date",
        "planned_delivery_date",
        "actual_delivery_date",
    ],
    "purchase_orders": ["po_date"],
    "vendor_invoices": ["invoice_date"],
    "expenses": ["expense_date"],
    "documents": ["created_date"],
}

TIMESTAMP_COLUMNS = {
    "emails": ["timestamp"],
    "events": ["timestamp"],
}


def import_csv_data():
    print("Starting Company Brain data import...")
    print(f"Reading CSV files from: {DATA_DIR}")

    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data folder not found: {DATA_DIR}")

    # Confirm that all CSV files exist before starting.
    for table_name in IMPORT_ORDER:
        csv_path = DATA_DIR / f"{table_name}.csv"

        if not csv_path.is_file():
            raise FileNotFoundError(f"Missing CSV file: {csv_path}")

    # A single transaction means a failure rolls back this import.
    with engine.begin() as connection:

        # Avoid duplicate imports into tables that already contain rows.
        for table_name in IMPORT_ORDER:
            count = connection.execute(
                text(f'SELECT COUNT(*) FROM "{table_name}"')
            ).scalar_one()

            if count > 0:
                raise RuntimeError(
                    f"Table '{table_name}' already contains {count} rows. "
                    "Import cancelled to prevent duplicates."
                )

        for table_name in IMPORT_ORDER:
            csv_path = DATA_DIR / f"{table_name}.csv"
            print(f"\nImporting {table_name}...")

            df = pd.read_csv(csv_path)

            for column in DATE_COLUMNS.get(table_name, []):
                df[column] = pd.to_datetime(
                    df[column], errors="raise"
                ).dt.date

            for column in TIMESTAMP_COLUMNS.get(table_name, []):
                df[column] = pd.to_datetime(
                    df[column], errors="raise"
                )

            # Convert missing values to database NULLs.
            df = df.astype(object).where(pd.notna(df), None)

            df.to_sql(
                name=table_name,
                con=connection,
                if_exists="append",
                index=False,
                chunksize=500,
            )

            print(f"Imported {len(df)} rows.")

    print("\nAll 15 tables imported successfully!")


if __name__ == "__main__":
    try:
        import_csv_data()
    except Exception as error:
        print(f"\nIMPORT FAILED: {error}")
        print("The import transaction was rolled back.")