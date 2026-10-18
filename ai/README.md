# Company Brain: AI layer (Member 2)

This is the AI part of Company Brain for ApexRoute Logistics. It takes a plain-English question and a user role, and returns an answer built only from company data and company documents. The LLM is never the source of truth. It writes SQL and wording, but every fact in an answer comes from the database or a document.

## How a question flows

```text
question + role
      |
   router: SQL, RAG or HYBRID
   /         |          \
 SQL        RAG       HYBRID
  |          |           |
database  documents   both (rule from documents, people from database)
   \         |          /
    LLM writes the answer from what was retrieved
                |
   answer + type + sources + sql + data
```

If the first path finds nothing, the other paths are tried. If none of them find anything, the answer is "not_found". The system never invents an answer to fill the gap.

There is no endpoint per question. The model writes the SQL, the code checks it, and the database enforces what each role can read, so new questions work without new code.

## Folder layout

```text
Company-Brain/           (team repo root)
  backend/               Member 1
  database/              Member 1
  ai/
    answer.py        answer(question, user_role): the one function the app calls
    router.py        decides SQL, RAG or HYBRID
    text_to_sql.py   question -> SQL -> checked, role-limited query -> answer
    sql_prompt.txt   instructions and business definitions for the SQL writer
    rag.py           document search with embeddings, answers from excerpts only
    access.py        which tables each role may read
    llm.py           the only file that talks to the LLM provider
    api.py           FastAPI server (POST /ask) and the test chat page
    chat.html        temporary test chat, served at /
  eval/
    questions.json   test questions with the expected route, type and text
    run_eval.py      runs them and prints PASS or FAIL
  documents/         CSV data files and the three SOP .txt files (kept local, not in Git)
  load_db.py         builds company.db from the CSVs
  inspect_csvs.py    helper: prints each CSV's columns
  peek_db.py         helper: prints sample values from the database
```

## Setup and run

Needs Python 3.11 or newer (built on 3.13). Run every command below from the repo root.

```powershell
pip install pandas python-dotenv truststore groq fastembed numpy fastapi uvicorn
```

1. Create a `.env` file in the repo root with your own key (see `.env.example`):
   ```text
   GROQ_API_KEY=your_key_here
   ```
   Never commit `.env`.
2. Put the `documents` folder (the CSVs and the SOP files) in the repo root. It is not in Git, because the team keeps the original datasets local until approved for sharing, so get it from Member 2.
3. Build the database from the CSVs: `python load_db.py`
   (`company.db` is generated, so it is not pushed to Git either.)
4. Start the server:
   ```powershell
   python -m uvicorn api:app --app-dir ai --port 8000
   ```
   The first start downloads the embedding model (about 70 MB, once), so give it a minute.
5. Open `http://127.0.0.1:8000/` for the test chat, or `http://127.0.0.1:8000/docs` for the API page.

`llm.py` uses `truststore` so Python trusts the Windows certificate store. This is needed on networks that intercept HTTPS.

## API

`POST /ask`

```json
{"question": "How many employees are in HR?"}
```

Header (temporary, for development only): `X-User-Role: employee | hr | finance | admin`

Response:

```json
{
  "answer": "There are 74 employees in HR.",
  "type": "sql",
  "route": "sql",
  "role": "employee",
  "sources": [{"document": "company database", "id": null, "score": null}],
  "sql": "SELECT COUNT(*) AS hr_count FROM employees WHERE department = 'HR'",
  "data": {"columns": ["hr_count"], "rows": [[74]]}
}
```

What `type` means:

| type | meaning |
|---|---|
| sql | answered from the database |
| rag | answered from the documents |
| hybrid | a rule from the documents plus matching records from the database |
| denied | the user's role can't read the data needed |
| not_found | nothing in the data or documents answers it |
| error | something broke (details are in the server log only, never sent to the browser) |

Notes for the frontend:
- `data` is a table (`columns` and `rows`) that can be shown as is. It is `null` for document answers.
- `sources` is a list of `{document, id, score}`. For database answers the document is `"company database"`.
- `answer` can contain `**bold**` markers.
- Other endpoints: `GET /health` returns `{"status": "ok"}`, and `GET /` serves the temporary test chat.

You can also call the function directly from Python: `answer(question, user_role)` in `ai/answer.py` returns the same dictionary.

## Roles and access

Roles live in one dictionary in `ai/access.py`. Edit it to change who can read what.

| role | tables it can read |
|---|---|
| employee | employees, company_master, business_rules |
| hr | the employee tables plus documents |
| finance | the employee tables plus customers, sales_orders, sales_invoices, payments, expenses, purchase_orders, vendor_invoices, vendors |
| admin | everything |

Shipments, emails and events are admin only for now. An unknown role gets the `employee` level, never more.

Access is enforced in code, not in the prompt, in three layers:
1. The SQL writer is only shown the tables its role may read.
2. Every generated query is checked: SELECT only, one statement, no write keywords, known tables only, allowed tables only.
3. The query runs on a read-only database connection with a SQLite authorizer, so the database itself refuses any table outside the role's list, whatever SQL the model writes.

**Important for integration:** the `X-User-Role` header in `api.py` is a development shortcut. Anyone who can reach the server can claim to be admin. Before this runs anywhere shared, replace the `current_role()` function in `api.py` so the role comes from the login token on the backend, never from anything the frontend sends.

## How the pieces work

**SQL path (`text_to_sql.py`).** The schema and the real values of small columns (departments, statuses) are read from the database and put in the prompt, along with the table links and business definitions from `sql_prompt.txt`. The model returns one SELECT query. If it fails, the error is sent back once for a corrected query. Up to 100 rows are fetched and the answer step sees the first 50, and it says when a list was cut off. The answer step is told to use only the query result and to say plainly when nothing matches.

**Document path (`rag.py`).** The knowledge base is 11 chunks: the three SOP files (order processing, procurement, refund) and the 8 rows of `business_rules.csv`, one chunk each. They are embedded with `fastembed` (a small local model) and kept in memory. For a question, the top 3 chunks by cosine similarity are retrieved, and anything below a score of 0.55 is dropped. If nothing is left, the model is not even called and the answer is "couldn't find it". Otherwise the model must answer only from the excerpts, name the document or rule, and reply `NOT_FOUND` if the excerpts only touch the topic without answering it.

**Hybrid path (`answer.py`).** For questions like "Which employees can approve refunds above 50000?": the top 2 matching rules are retrieved from the documents, passed to the SQL writer as "Rule context", and the answer states the rule first and then lists the matching people. The sources include both the rule and the database.

**Router (`router.py`).** One short LLM call returns SQL, RAG or HYBRID, using examples in the prompt. If a question gets sent the wrong way, add it as an example in `ROUTER_SYSTEM` and as a line in the eval file.

**LLM (`llm.py`).** Groq with `openai/gpt-oss-120b`, temperature 0. Provider and model are set at the top of the file. Replies are cleaned of invisible special spaces and hyphens, which the model sometimes outputs and which break plain-text matching.

## Business definitions

These live in `ai/sql_prompt.txt`. Several are my placeholders and need a team decision. If you change one, change it there and nowhere else.

- **Fiscal year** runs April to March, so "this year" means 1 April 2026 to 31 March 2027.
- **Profit** = invoiced revenue minus expenses minus vendor invoices. This is a placeholder. With the current data it comes out as a loss of about 7.5 crore, because vendor invoices are larger than total revenue. The data was generated separately, so the tables don't balance.
- **Outstanding invoices** currently means status `Outstanding` only. Partially paid invoices are not counted. Open decision.
- **Delayed orders** uses `sales_orders.status = 'Delayed'` (176), not the shipments table, because the two tables disagree.
- **Cancelled orders** are excluded from order value totals.
- **Finance Manager** means department Finance with job role Manager or Senior Manager. There is no job title called "Finance Manager". Someone can approve an amount only if their `approval_authority_inr` also covers it. Open decision.
- **Lakh and crore:** 1 lakh = 100000, 1 crore = 10000000. All amounts are in INR.

## Testing

`eval/questions.json` has 13 questions. Each one sets a role and the expected route, type and text. Three of them check access control (an employee asking for profit, HR asking for orders, an unknown role).

```powershell
python eval/run_eval.py              # all questions
python eval/run_eval.py 1 2 3        # only these question numbers
```

All 13 pass. Run the full list after any change to a prompt, the router or the access rules. When a real question fails, add it to the file, so it can't quietly break again.

The runner stops with a clear message if the Groq daily limit is hit.

## Known limits and open decisions

- **Groq free tier has a daily token cap** (about 200,000 tokens per day on this model at the time of writing). A long testing session, or a demo, can run into it. Paid credit fixes it. To switch, set `PROVIDER = "anthropic"` in `llm.py` and add `ANTHROPIC_API_KEY` to `.env`.
- **No salary data.** The employees table has no pay column, so questions like "top five paid employees" correctly return `not_found`. `approval_authority_inr` is a spending approval limit and is not pay. Adding salaries would need column-level access (HR and admin only), which is not built yet.
- **Access is per table, not per column.** The `employee` role can see every column of the employees table, including approval limits and work emails.
- **Documents are open to every role.** `documents.csv` has an `access_level` column that is not enforced yet.
- **No memory between messages.** Every question stands alone, so a follow-up like "the one in Finance" won't work. Supporting that means the chat screen sends the last few messages with each question.
- **No audit logging** yet (who asked what, which route, which SQL).
- **Small knowledge base.** Only 11 chunks, held in memory. There is no PDF or Word extraction and no vector database, because they weren't needed at this size. They would be needed if real handbooks are added.
- **Not wired in:** `emails.csv` and `events.csv`.
- **Shipments** only have IDs for carriers, drivers, vehicles and warehouses, so those can't be turned into names.
- **The router can misroute.** Expect some surprises from real users.

## For Member 1 and Member 3

**Member 1:** the AI layer reads `company.db` directly. Keep your login and your dashboard endpoints, but for the chat box, call `answer(question, role)` or forward to `POST /ask`, with the role taken from the login. If your table or column names differ from `company.db`, tell me, because the SQL prompt is built from the real schema and the business definitions mention column names. The AI layer currently runs on SQLite (`company.db`, built by `load_db.py`). If the team database is PostgreSQL, moving the AI layer over is real work, not a one-line change: `list_tables` and `schema_text` read SQLite's catalog, `connect_ro` and `run_sql` open SQLite, the role enforcement uses SQLite's authorizer (on PostgreSQL it would become database roles with grants, or a read-only user per role), and `sql_prompt.txt` is written for SQLite, including its date functions. The router, document search, answer step and API do not change. We need to agree which database the AI queries.

**Member 3:** `type` decides how a message should look (the test chat in `ai/chat.html` shows one way: red for denied, yellow for not found). `data` becomes a table and `sources` becomes citations. You can build against the sample response above before the backend is ready.
