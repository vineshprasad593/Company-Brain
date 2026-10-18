# Company Brain



Company Brain is an internal company knowledge and decision-support system designed to help employees find company information faster and make more informed operational decisions.



## Project Goals



- Reduce time spent searching for company information.

- Improve visibility across departments.

- Support informed operational decisions.

- Provide answers grounded in company data and internal documents.



## Architecture



- **Backend API:** Python and FastAPI.

- **Structured data:** PostgreSQL.

- **Document knowledge:** Intended integration with a Retrieval-Augmented Generation (RAG) pipeline.

- **Hybrid queries:** Designed to combine structured database results and document retrieval where needed.



The backend and database form the foundation for the AI/RAG integration.



## Repository Structure



```text

Company-Brain/

├── backend/

│   ├── config/

│   ├── database/

│   ├── models/

│   ├── routes/

│   ├── services/

│   ├── main.py

│   └── requirements.txt

├── database/

│   └── schema.sql

└── README.md

```



## Prerequisites



- Python 3.10 or a compatible version supported by the project's dependencies.

- PostgreSQL.

- Git.



## Setup



### 1. Clone the repository



```bash

git clone https://github.com/vineshprasad593/Company-Brain.git

cd Company-Brain

```



### 2. Create a PostgreSQL database



Create an empty development database named `company\_brain`, or choose another database name and use it consistently in your configuration.



### 3. Restore the database schema



Run this command from the repository root, targeting the empty database:



```bash

psql -U postgres -d company\_brain -f database/schema.sql

```



**Important:** Run the schema against a fresh, empty development database. Do not run it against an existing database that already contains these tables.



### 4. Set up the Python environment



```powershell

cd backend

python -m venv venv

.\\venv\\Scripts\\Activate.ps1

python -m pip install -r requirements.txt

```



On macOS or Linux, activate the environment with:



```bash

source venv/bin/activate

```



### 5. Configure environment variables



Create a local `.env` file inside the `backend` directory:



```env

DATABASE\_URL=postgresql+psycopg2://YOUR\_USERNAME:YOUR\_PASSWORD@localhost:5432/company\_brain

```



Replace the placeholders with your local PostgreSQL credentials. URL-encode special characters in the username or password when required.



Never commit `.env` files, passwords, API keys, or other credentials.



### 6. Start the API



From the `backend` directory, run:



```bash

uvicorn main:app --reload

```



Open the FastAPI documentation at:



http://127.0.0.1:8000/docs



## Database Schema



The `database/schema.sql` file contains the PostgreSQL table definitions. It does not include the original dataset records.



The original company datasets are intentionally excluded from version control. Obtain approved development data separately and place it in the appropriate local data directory if required by the ingestion workflow.



## API and Ingestion



The backend includes API functionality for querying and ingesting structured company data. Available endpoints and request schemas can be inspected through the FastAPI documentation after starting the server.



## Development Notes



- Keep local credentials in `.env`.

- Keep virtual environments and generated files out of Git.

- Use synthetic or explicitly authorized company data for testing.

- Validate ingestion against a separate development database before using real company data.

- Coordinate the RAG integration through the agreed backend/API interface.



## Project Status



This repository contains the backend and database foundation. RAG integration and end-to-end functionality should be verified against the current implementation before being considered complete.




