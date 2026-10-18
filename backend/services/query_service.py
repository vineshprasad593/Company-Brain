
from sqlalchemy import text
from database.connection import engine


def process_query(question: str):
    normalized = question.lower().strip().rstrip(" ?.!")

    def run_query(sql, params=None):
        with engine.connect() as connection:
            result = connection.execute(text(sql), params or {})
            return result.mappings().all()

    def count_rows(table):
        rows = run_query(f"SELECT COUNT(*) AS total FROM {table}")
        return rows[0]["total"]

    count_phrases = ["how many", "count", "number of", "total"]

    # Feature 1: Count all employees
    if (
        "employee" in normalized
        and any(p in normalized for p in count_phrases)
        and any(p in normalized for p in [
            "in the company", "at the company", "in our company",
            "in this company", "in the organization",
            "in our organization", "overall", "all employees"
        ])
    ):
        total = count_rows("employees")
        return {
            "question": question,
            "answer": f"There are {total} employees in the company.",
            "total_employees": total,
        }

    # Feature 2: Find employee by name
    employee_name = None

    if normalized.startswith("who is "):
        employee_name = question.strip()[len("who is "):].strip().rstrip(" ?.!")

    elif normalized.startswith("find employee "):
        employee_name = question.strip()[len("find employee "):].strip().rstrip(" ?.!")

    if employee_name is not None:
        rows = run_query("""
            SELECT employee_id, name, department, job_role,
                   work_email, employment_status
            FROM employees
            WHERE name ILIKE :name
            LIMIT 2
        """, {"name": employee_name})

        if not rows:
            return {
                "question": question,
                "answer": f"No employee found with the name '{employee_name}'.",
            }

        if len(rows) > 1:
            return {
                "question": question,
                "answer": (
                    f"Multiple employees match '{employee_name}'. "
                    "Please be more specific."
                ),
            }

        employee = dict(rows[0])
        return {
            "question": question,
            "answer": (
                f"{employee['name']} works in "
                f"{employee['department']} as {employee['job_role']}."
            ),
            "employee": employee,
        }

    # Feature 3: Department with the most employees
    if any(phrase in normalized for phrase in [
        "which department has the most employees",
        "department with the most employees",
        "department has the highest number of employees",
        "which department has the highest number of employees"
    ]):
        rows = run_query("""
            SELECT department, COUNT(*) AS total
            FROM employees
            WHERE department IS NOT NULL
              AND TRIM(department) <> ''
            GROUP BY department
            ORDER BY total DESC, department ASC
            LIMIT 1
        """)

        if not rows:
            return {
                "question": question,
                "answer": "No department data is available.",
            }

        department = rows[0]["department"]
        total = rows[0]["total"]

        return {
            "question": question,
            "answer": (
                f"{department} has the most employees, "
                f"with {total} employees."
            ),
            "department": department,
            "employee_count": total,
        }

    # Feature 4: Count employees/people/staff by department
    count_subjects = ["employee", "employees", "people", "person", "staff"]

    if (
        any(word in normalized for word in count_subjects)
        and any(p in normalized for p in count_phrases)
    ):
        for phrase in [
            " working in ", " working at ",
            " work in ", " work at ",
            " in ", " from "
        ]:
            if phrase not in normalized:
                continue

            department = normalized.rsplit(phrase, 1)[1].strip()
            department = department.removeprefix("the ").strip()
            department = department.rstrip(" ?.!").strip()
            department = department.removesuffix(" department").strip()

            if not department or department in [
                "company", "the company", "our company",
                "organization", "the organization",
                "our organization", "the whole company",
                "all departments"
            ]:
                continue

            rows = run_query("""
                SELECT department, COUNT(*) AS total
                FROM employees
                WHERE department ILIKE :department
                GROUP BY department
            """, {"department": department})

            if not rows:
                return {
                    "question": question,
                    "answer": (
                        f"No employees found in the "
                        f"{department} department."
                    ),
                    "department": department,
                    "employee_count": 0,
                }

            actual_department = rows[0]["department"]
            total = rows[0]["total"]

            return {
                "question": question,
                "answer": (
                    f"There are {total} employees in "
                    f"the {actual_department} department."
                ),
                "department": actual_department,
                "employee_count": total,
            }

    # Feature 5: List employees by department
    for phrase in [
        "show me employees in ",
        "show employees in ",
        "list employees in ",
        "find employees in ",
        "list employees from "
    ]:
        if phrase in normalized:
            department = normalized.split(phrase, 1)[1].strip()
            department = department.removeprefix("the ").strip()
            department = department.rstrip(" ?.!").strip()

            rows = run_query("""
                SELECT employee_id, name, department, job_role,
                       work_email, employment_status
                FROM employees
                WHERE department ILIKE :department
                ORDER BY name
                LIMIT 20
            """, {"department": department})

            employees = [dict(row) for row in rows]

            return {
                "question": question,
                "answer": (
                    f"Found {len(employees)} employees in "
                    f"{department}. Showing up to 20 results."
                ),
                "department": department,
                "employees": employees,
            }

    # Feature 6: Count customers
    if (
        "customer" in normalized
        and any(p in normalized for p in count_phrases)
    ):
        total = count_rows("customers")
        return {
            "question": question,
            "answer": f"There are {total} customers.",
            "customer_count": total,
        }

    # Feature 7: Count vendors
    if (
        "vendor" in normalized
        and any(p in normalized for p in count_phrases)
    ):
        total = count_rows("vendors")
        return {
            "question": question,
            "answer": f"There are {total} vendors.",
            "vendor_count": total,
        }

    # Feature 8: Total sales order value
    if (
        "sales" in normalized
        and any(p in normalized for p in [
            "total", "value", "revenue", "sum"
        ])
    ):
        rows = run_query("""
            SELECT COALESCE(SUM(order_value_inr), 0) AS total
            FROM sales_orders
        """)

        total = rows[0]["total"]

        return {
            "question": question,
            "answer": f"The total sales order value is ₹{total:,.2f}.",
            "total_sales_order_value_inr": float(total),
        }

    # Feature 9: Completed payment summary
    if (
        "payment" in normalized
        and any(p in normalized for p in [
            "total", "sum", "amount", "how much"
        ])
    ):
        rows = run_query("""
            SELECT COALESCE(SUM(amount_inr), 0) AS total,
                   COUNT(*) AS payment_count
            FROM payments
            WHERE LOWER(payment_status)
                IN ('completed', 'paid', 'success', 'successful')
        """)

        total = rows[0]["total"]
        payment_count = rows[0]["payment_count"]

        return {
            "question": question,
            "answer": (
                f"Completed payments total ₹{total:,.2f} "
                f"across {payment_count} records."
            ),
            "completed_payment_total_inr": float(total),
            "completed_payment_count": payment_count,
        }

    # Feature 10: Total expenses
    if (
        "expense" in normalized
        and any(p in normalized for p in [
            "total", "sum", "amount", "how much"
        ])
    ):
        rows = run_query("""
            SELECT COALESCE(SUM(amount_inr), 0) AS total
            FROM expenses
        """)

        total = rows[0]["total"]

        return {
            "question": question,
            "answer": f"Total recorded expenses are ₹{total:,.2f}.",
            "total_expenses_inr": float(total),
        }

    # Feature 11: Delayed shipments
    if (
        "shipment" in normalized
        and any(p in normalized for p in [
            "delay", "delayed", "late", "overdue"
        ])
    ):
        rows = run_query("""
            SELECT shipment_id, order_id, planned_delivery_date,
                   actual_delivery_date, delivery_status, delay_days
            FROM shipments
            WHERE LOWER(delivery_status) LIKE '%delay%'
               OR COALESCE(delay_days, 0) > 0
            ORDER BY delay_days DESC NULLS LAST
            LIMIT 20
        """)

        shipments = [dict(row) for row in rows]

        return {
            "question": question,
            "answer": (
                f"Found {len(shipments)} delayed shipments. "
                "Showing up to 20 results."
            ),
            "shipments": shipments,
        }

    # Fallback: unsupported question
    return {
        "question": question,
        "answer": (
            "I can answer employee questions, count customers and vendors, "
            "summarize sales, completed payments and expenses, "
            "and list delayed shipments."
        ),
    }
