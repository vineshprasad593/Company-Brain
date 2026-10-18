import os, time
from pathlib import Path

import truststore
truststore.inject_into_ssl()

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH, override=True)

PROVIDER = "groq"   # change to "anthropic" when you get paid credit

GROQ_MODEL = "openai/gpt-oss-120b"
ANTHROPIC_MODEL = "claude-sonnet-5-5"


def clean_text(text: str) -> str:
    """Swap invisible special spaces and hyphens for plain ones."""
    for ch in ("\u00a0", "\u202f", "\u2009", "\u2007"):
        text = text.replace(ch, " ")
    return text.replace("\u2011", "-").replace("\u2010", "-")


def ask_llm(system: str, user: str, max_tokens: int = 4000) -> str:
    if PROVIDER == "groq":
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError(f"GROQ_API_KEY not found. Looked in: {ENV_PATH} (exists: {ENV_PATH.exists()})")
        client = Groq(api_key=key, timeout=30)
        last_error = None
        for attempt in range(4):
            try:
                r = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=max_tokens,
                    temperature=0,
                )
                return clean_text((r.choices[0].message.content or "").strip())
            except Exception as e:
                last_error = e
                msg = str(e)
                print(f"Attempt {attempt + 1} failed: {msg[:200]}")
                if "429" in msg or "503" in msg or "timeout" in msg.lower():
                    time.sleep(3 * (attempt + 1))
                    continue
                raise
        raise last_error

    from anthropic import Anthropic
    client = Anthropic()
    r = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return clean_text(r.content[0].text.strip())


if __name__ == "__main__":
    print("START")
    print("ANSWER:", ask_llm("You are a helpful assistant.", "Say hello in one short sentence."))
    print("DONE")