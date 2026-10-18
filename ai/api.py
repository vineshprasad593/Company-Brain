from pathlib import Path

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from answer import answer

app = FastAPI(title="Company Brain AI")

# lets a chat page running on another port call this server from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=500)


def current_role(x_user_role):
    # DEV ONLY: there is no login yet, so the role comes from a header.
    # Member 1 replaces this one function so the role comes from the login token.
    return x_user_role or "employee"


@app.get("/")
def chat_page():
    # temporary test chat, served from the same address as the API
    return FileResponse(Path(__file__).resolve().parent / "chat.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(body: Ask, x_user_role: str | None = Header(default=None)):
    result = answer(body.question, current_role(x_user_role))
    error = result.pop("error", None)
    if error:
        print("AI error:", error)   # logged here, never sent to the browser
    return result