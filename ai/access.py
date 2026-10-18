import sqlite3

# Which tables each role may read. Edit this one dictionary to change access.
ROLE_TABLES = {
    "employee": {"employees", "company_master", "business_rules"},
    "hr": {"employees", "company_master", "business_rules", "documents"},
    "finance": {"employees", "company_master", "business_rules", "customers",
                "sales_orders", "sales_invoices", "payments", "expenses",
                "purchase_orders", "vendor_invoices", "vendors"},
    "admin": None,   # None means every table
}
DEFAULT_ROLE = "employee"   # an unknown role gets the least access, never the most


def normalize_role(role):
    role = (role or "").strip().lower()
    return role if role in ROLE_TABLES else DEFAULT_ROLE


def allowed_tables(role, all_tables):
    allowed = ROLE_TABLES[normalize_role(role)]
    return set(all_tables) if allowed is None else set(allowed) & set(all_tables)


def make_authorizer(allowed):
    """SQLite calls this for every table a query touches. Anything not allowed is refused."""
    def authorizer(action, arg1, arg2, dbname, source):
        if action == sqlite3.SQLITE_READ:
            return sqlite3.SQLITE_OK if arg1 in allowed else sqlite3.SQLITE_DENY
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION):
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    return authorizer
    