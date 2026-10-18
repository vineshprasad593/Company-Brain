from router import route
from text_to_sql import answer_from_sql
from rag import retrieve, answer_from_docs
from access import normalize_role

DB_SOURCE = {"document": "company database", "id": None, "score": None}


def _denied(r):
    return {"answer": r["answer"], "type": "denied", "sources": [],
            "sql": None, "data": None}


def _try_sql(question, role):
    r = answer_from_sql(question, role=role)
    if r.get("denied"):
        return _denied(r), True
    result = {"answer": r["answer"], "type": "sql", "sources": [DB_SOURCE],
              "sql": r["sql"], "data": r["data"]}
    return result, r["sql"] is not None


def _try_rag(question, role):
    r = answer_from_docs(question)
    result = {"answer": r["answer"], "type": "rag", "sources": r["sources"],
              "sql": None, "data": None}
    return result, len(r["sources"]) > 0


def _try_hybrid(question, role):
    # step 1: find the rule in the documents
    hits = retrieve(question, k=2)
    if not hits:
        return None, False
    context = "\n".join(f"{c['text']} ({c['source']}, {c['id']})" for s, c in hits)
    # step 2: use the rule to find the matching records, within this role's access
    r = answer_from_sql(question, context, role=role)
    if r.get("denied"):
        return _denied(r), True
    if r["sql"] is None:
        return None, False
    rule_sources = [{"document": c["source"], "id": c["id"], "score": round(s, 2)}
                    for s, c in hits]
    result = {"answer": r["answer"], "type": "hybrid", "sources": rule_sources + [DB_SOURCE],
              "sql": r["sql"], "data": r["data"]}
    return result, True


def answer(question: str, user_role: str = "employee") -> dict:
    """The one function the rest of the app calls.
    Returns: answer, type, route, role, sources, sql, data (and error if something broke).
    type is one of: sql, rag, hybrid, denied, not_found, error."""
    role = normalize_role(user_role)
    try:
        first = route(question)
        order = {"sql": [_try_sql, _try_rag],
                 "rag": [_try_rag, _try_sql],
                 "hybrid": [_try_hybrid, _try_sql, _try_rag]}[first]
        for path in order:
            result, found = path(question, role)
            if found:
                result["route"] = first
                result["role"] = role
                return result
        return {"answer": "I couldn't find that in the company data or documents.",
                "type": "not_found", "route": first, "role": role,
                "sources": [], "sql": None, "data": None}
    except Exception as e:
        return {"answer": "Something went wrong while looking that up. Please try again.",
                "type": "error", "route": None, "role": role, "sources": [],
                "sql": None, "data": None, "error": str(e)}


if __name__ == "__main__":
    import time
    tests = [
        ("How many employees are in HR?", "employee"),
        ("What are the steps to process a refund?", "employee"),
        ("What is our profit this year?", "employee"),
        ("What is our profit this year?", "finance"),
        ("Which employees can approve refunds above 50000?", "employee"),
        ("How many orders are delayed?", "hr"),
        ("How many orders are delayed?", "some_made_up_role"),
    ]
    for q, role in tests:
        r = answer(q, role)
        print(f"\nQ ({role}):", q)
        print("route:", r["route"], "| type:", r["type"], "| role used:", r["role"])
        print("A:", r["answer"])
        time.sleep(2)