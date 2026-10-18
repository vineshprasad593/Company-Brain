from llm import ask_llm

ROUTER_SYSTEM = (
    "You route questions for a company assistant. Reply with exactly one word: SQL, RAG or HYBRID.\n\n"
    "SQL = the answer is a number, a total, or a list of people or records taken from company data "
    "tables: employees (including each person's approval_authority_inr limit), customers, orders, "
    "invoices, payments, shipments, vendors, purchase orders, expenses, revenue, profit.\n"
    "RAG = the answer is a written rule or procedure from a policy document: SOPs, approval rules "
    "and thresholds, how a process is supposed to work.\n"
    "HYBRID = the question needs BOTH: a rule from a policy document to decide what to look for, "
    "and company data tables to find the matching people or records.\n\n"
    "Examples:\n"
    "How many employees are in HR? -> SQL\n"
    "Who is the manager of Arun Nair? -> SQL\n"
    "Who has approval authority of 5 lakh or more? -> SQL\n"
    "What is the total of outstanding invoices? -> SQL\n"
    "What are the steps to process a refund? -> RAG\n"
    "Refunds above what amount need approval? -> RAG\n"
    "What does the policy say about delayed shipments? -> RAG\n"
    "Which employees can approve refunds above 50000? -> HYBRID\n"
    "Who is allowed to approve orders above 2.5 lakh? -> HYBRID\n"
    "Which shipments need a customer notification under our rules? -> HYBRID\n\n"
    "Reply SQL, RAG or HYBRID and nothing else."
)


def route(question: str) -> str:
    reply = ask_llm(ROUTER_SYSTEM, question, max_tokens=1000).upper()
    if "HYBRID" in reply:
        return "hybrid"
    if "RAG" in reply:
        return "rag"
    return "sql"