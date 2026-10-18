import re, sqlite3, time
from datetime import date
from pathlib import Path
from llm import ask_llm
from access import allowed_tables, make_authorizer

HERE = Path(__file__).resolve().parent
DB_PATH = HERE.parent / "company.db"
FORBIDDEN = ["insert", "update", "delete", "drop", "alter", "create", "replace",
             "attach", "detach", "pragma", "truncate", "vacuum"]


class AccessDenied(Exception):
    pass


def connect_ro():
    # read-only connection: even a validation miss can't change data
    return sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True)


def list_tables():
    conn = connect_ro()
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    conn.close()
    return tables


ALL_TABLES = list_tables()


def schema_text(tables):
    conn = connect_ro()
    lines = []
    for t in tables:
        n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        lines.append(f"\nTable {t} ({n} rows)")
        for _, col, ctype, *_ in conn.execute(f'PRAGMA table_info("{t}")').fetchall():
            distinct = [r[0] for r in conn.execute(
                f'SELECT DISTINCT "{col}" FROM "{t}" WHERE "{col}" IS NOT NULL LIMIT 13')]
            vals = [str(v)[:40] for v in distinct]
            if len(vals) <= 12:
                note = "values: " + ", ".join(vals)
            else:
                note = "e.g. " + ", ".join(vals[:3])
            lines.append(f"  {col} ({ctype}) {note}")
    conn.close()
    return "\n".join(lines)


_PROMPTS = {}


def system_prompt_for(role):
    """Builds (and remembers) the SQL prompt showing only the tables this role may read."""
    allowed = sorted(allowed_tables(role, ALL_TABLES))
    blocked = sorted(set(ALL_TABLES) - set(allowed))
    key = tuple(allowed)
    if key not in _PROMPTS:
        today = date.today()
        y = today.year if today.month >= 4 else today.year - 1
        text = (HERE / "sql_prompt.txt").read_text(encoding="utf-8")
        text = (text.replace("<<TODAY>>", today.isoformat())
                    .replace("<<SCHEMA>>", schema_text(allowed))
                    .replace("<<FY_START>>", f"{y}-04-01")
                    .replace("<<FY_END>>", f"{y + 1}-03-31"))
        rules = ["", "Access rule:",
                 "- You may ONLY use these tables: " + ", ".join(allowed) + "."]
        if blocked:
            rules.append("- Restricted tables you may NOT use: " + ", ".join(blocked) + ".")
        rules.append("- If the question is about company records that live in a restricted table, output exactly: NO_ACCESS")
        rules.append("- If the question is not about company records at all (general knowledge, policies, or anything the tables cannot answer), output exactly: NO_SQL")
        text += "\n".join(rules) + "\n"
        _PROMPTS[key] = text
    return _PROMPTS[key]


def clean_sql(raw: str) -> str:
    sql = re.sub(r"```(?:sql)?", "", raw).strip()
    return sql.rstrip(";").strip()


def validate_sql(sql: str, allowed) -> None:
    low = sql.lower()
    if not low.startswith("select"):
        raise ValueError("Only SELECT queries are allowed")
    if ";" in sql:
        raise ValueError("Only one statement is allowed")
    for word in FORBIDDEN:
        if re.search(rf"\b{word}\b", low):
            raise ValueError(f"Forbidden keyword: {word}")
    for t in re.findall(r'\b(?:from|join)\s+"?([a-z_]+)"?', low):
        if t not in ALL_TABLES:
            raise ValueError(f"Unknown table: {t}")
        if t not in allowed:
            raise AccessDenied(t)


def run_sql(sql: str, role=None, limit: int = 100):
    allowed = allowed_tables(role, ALL_TABLES)
    validate_sql(sql, allowed)
    conn = connect_ro()
    # the database itself refuses any table outside the allowed set
    conn.set_authorizer(make_authorizer(allowed))
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchmany(limit)
    except sqlite3.DatabaseError as e:
        if "not authorized" in str(e).lower():
            raise AccessDenied(str(e))
        raise
    finally:
        conn.close()
    return cols, rows


def question_to_sql(question: str, context: str = "", role=None):
    """Returns (sql, cols, rows). Retries once if the query fails.
    Raises AccessDenied if the role may not read the data needed.
    context is optional rule text from a company document (used by hybrid questions)."""
    system = system_prompt_for(role)
    prompt = question if not context else f"{question}\n\nRule context:\n{context}"
    sql = clean_sql(ask_llm(system, prompt))
    if sql == "NO_SQL":
        return None, [], []
    if sql == "NO_ACCESS":
        raise AccessDenied("needs a table this role cannot read")
    try:
        cols, rows = run_sql(sql, role)
        return sql, cols, rows
    except AccessDenied:
        raise
    except Exception as e:
        fix = (f"Question: {prompt}\nYour query: {sql}\nError: {e}\n"
               "Write a corrected query. Output only the SQL.")
        sql = clean_sql(ask_llm(system, fix))
        if sql == "NO_SQL":
            return None, [], []
        if sql == "NO_ACCESS":
            raise AccessDenied("needs a table this role cannot read")
        cols, rows = run_sql(sql, role)
        return sql, cols, rows


ANSWER_SYSTEM = (
    "You answer questions about a company using ONLY the query result you are given.\n"
    "- Do not use outside knowledge and do not guess.\n"
    "- If the result is empty, say no matching records were found.\n"
    "- If several people match a name, list them and ask which one the user means.\n"
    "- Amounts are in Indian rupees (INR).\n"
    "- If a rule from company documents is given, state the rule first, then list every row in the query result. The query has already applied the rule, so do not filter, drop or re-check rows yourself, even if a job title is worded differently from the rule. If the result is empty, say plainly that nobody meets it.\n"
    "- If the result is one row with several columns, mention every value.\n"
    "- If the result has 50 or more rows, say the list was cut off at 50 and there may be more.\n"
    "- Write rupee amounts with the ₹ sign, and use lakh or crore for large numbers.\n"
    "- Be short and direct. Use up to three sentences, or a short list when naming people."
)

DENIED_MESSAGE = "Your role doesn't have access to the data needed to answer that."


def answer_from_sql(question: str, context: str = "", role=None):
    try:
        sql, cols, rows = question_to_sql(question, context, role)
    except AccessDenied:
        return {"answer": DENIED_MESSAGE, "type": "sql", "sql": None,
                "data": None, "denied": True}
    if sql is None:
        return {"answer": "I couldn't answer that from the company data.",
                "type": "sql", "sql": None, "data": None, "denied": False}
    result_text = f"Columns: {cols}\nRow count: {len(rows)}\nRows: {rows[:50]}"
    rule_part = f"\n\nRule from company documents:\n{context}" if context else ""
    answer = ask_llm(ANSWER_SYSTEM, f"Question: {question}{rule_part}\n\nQuery result:\n{result_text}")
    return {"answer": answer, "type": "sql", "sql": sql,
            "data": {"columns": cols, "rows": rows}, "denied": False}


if __name__ == "__main__":
    tests = [
        ("How many employees are in HR?", "employee"),
        ("What is our profit this year?", "employee"),
        ("What is our profit this year?", "finance"),
        ("How many orders are delayed?", "employee"),
        ("How many orders are delayed?", "admin"),
    ]
    for q, role in tests:
        print(f"\nQ ({role}):", q)
        try:
            r = answer_from_sql(q, role=role)
            print("SQL:", r["sql"])
            print("A:", r["answer"])
        except Exception as e:
            print("ERROR:", e)
        time.sleep(2)