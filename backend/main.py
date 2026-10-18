
from fastapi import FastAPI
from sqlalchemy import text

from routes.ingestion import router as ingestion_router
from routes.query import router as query_router
from database.connection import engine


app = FastAPI(
    title="Company Brain API",
    description="Backend API for the Company Brain system",
    version="1.0.0"
)


app.include_router(query_router)
app.include_router(ingestion_router)


@app.get("/db-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {
            "database": "connected",
            "result": result.scalar()
        }