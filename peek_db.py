import sqlite3

conn = sqlite3.connect("company.db")

checks = [
    ("business_rules", "SELECT rule_id, rule_name, rule_text FROM business_rules"),
    ("company_master", "SELECT * FROM company_master"),
    ("sales_orders status", "SELECT status, COUNT(*) FROM sales_orders GROUP BY status"),
    ("sales_invoices status", "SELECT status, COUNT(*) FROM sales_invoices GROUP BY status"),
    ("payments status", "SELECT payment_status, COUNT(*) FROM payments GROUP BY payment_status"),
    ("expense categories", "SELECT category, COUNT(*) FROM expenses GROUP BY category"),
    ("order date sample", "SELECT order_date FROM sales_orders LIMIT 3"),
    ("employee departments", "SELECT department, COUNT(*) FROM employees GROUP BY department"),
]

for title, sql in checks:
    print("\n==", title)
    for row in conn.execute(sql).fetchall():
        print(row)
conn.close()
