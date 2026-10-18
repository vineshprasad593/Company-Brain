
from sqlalchemy import text
from database.connection import engine

tables = [
    "employees", "vendors", "customers",
    "company_master", "business_rules",
    "sales_orders", "purchase_orders",
    "sales_invoices", "payments", "shipments",
    "vendor_invoices", "expenses", "documents",
    "emails", "events"
]

with engine.connect() as connection:
    for table in tables:
        result = connection.execute(
            text(f'SELECT COUNT(*) FROM "{table}"')
        )
        print(f"{table}: {result.scalar_one()} rows")
