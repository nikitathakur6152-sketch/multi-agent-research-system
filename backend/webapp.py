"""Small authenticated HTTP API for the research frontend."""

import hashlib
import hmac
import secrets

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from httpx import HTTPStatusError
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from database import (
    create_session,
    create_user,
    delete_session,
    find_user,
    get_research,
    list_research,
    save_research,
    user_for_session,
)
from pipeline import run_research_pipeline

app = FastAPI(title="Research App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

COOKIE_NAME = "research_session"
COOKIE_DAYS = 30


class AccountRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"{salt.hex()}${digest.hex()}"


def _check_password(password: str, saved_hash: str) -> bool:
    try:
        salt_hex, digest_hex = saved_hash.split("$", 1)
        expected = bytes.fromhex(digest_hex)
        actual = bytes.fromhex(_password_hash(password, bytes.fromhex(salt_hex)).split("$", 1)[1])
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _set_login_cookie(response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    create_session(user_id, _token_hash(token))
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=COOKIE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=False,  # Local HTTP development. Set secure=True behind HTTPS in production.
        samesite="lax",
        path="/",
    )


def _current_user(request: Request) -> dict[str, object]:
    token = request.cookies.get(COOKIE_NAME)
    user = user_for_session(_token_hash(token)) if token else None
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in.")
    return user


@app.get("/api/auth/me")
def current_user(user: dict[str, object] = Depends(_current_user)) -> dict[str, object]:
    return user


@app.post("/api/auth/register")
def register(payload: AccountRequest, response: Response) -> dict[str, object]:
    email = payload.email.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    user_id = create_user(email, _password_hash(payload.password))
    if user_id is None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    _set_login_cookie(response, user_id)
    return {"id": user_id, "email": email}


@app.post("/api/auth/login")
def login(payload: AccountRequest, response: Response) -> dict[str, object]:
    email = payload.email.strip().lower()
    user = find_user(email)
    if user is None or not _check_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    _set_login_cookie(response, user["id"])
    return {"id": user["id"], "email": user["email"]}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        delete_session(_token_hash(token))
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax")
    return {"status": "ok"}


@app.get("/api/research")
def research_history(user: dict[str, object] = Depends(_current_user)) -> list[dict[str, object]]:
    return list_research(int(user["id"]))


@app.get("/api/research/{run_id}")
def saved_research(
    run_id: int, user: dict[str, object] = Depends(_current_user)
) -> dict[str, object]:
    result = get_research(run_id, int(user["id"]))
    if result is None:
        raise HTTPException(status_code=404, detail="Saved research was not found.")
    return result


@app.post("/api/research")
async def research(
    request: ResearchRequest, user: dict[str, object] = Depends(_current_user)
) -> dict[str, object]:
    topic = request.topic.strip()
    if len(topic) < 2:
        raise HTTPException(status_code=422, detail="Enter a research question.")

    try:
        result = await run_in_threadpool(run_research_pipeline, topic)
    except HTTPStatusError as error:
        status = error.response.status_code
        if status == 429:
            detail = "Mistral rate limit reached. Check your limits and try again later."
        else:
            detail = f"An API returned HTTP {status}: {error.response.text}"
        raise HTTPException(status_code=status, detail=detail) from None
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Research failed: {error}") from None

    return save_research(int(user["id"]), topic, result)
