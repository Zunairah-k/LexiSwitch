from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import ACTIVE_LANGUAGES, LANGUAGES
from .model import LanguageIdentifier
from .pipeline import analyze_text

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["model"] = LanguageIdentifier.load()
    yield
    state.clear()


app = FastAPI(title="LexiSwitch API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class CompareRequest(BaseModel):
    text_a: str = Field(min_length=1, max_length=2000)
    text_b: str = Field(min_length=1, max_length=2000)


def _check(text: str) -> None:
    if not text.strip():
        raise HTTPException(status_code=422, detail="Text is empty.")


@app.get("/api/health")
def health():
    return {"status": "ok",
            "languages": [{"code": c, "name": LANGUAGES[c]} for c in ACTIVE_LANGUAGES]}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    _check(req.text)
    return analyze_text(state["model"], req.text)


@app.post("/api/compare")
def compare(req: CompareRequest):
    _check(req.text_a)
    _check(req.text_b)
    return {"a": analyze_text(state["model"], req.text_a),
            "b": analyze_text(state["model"], req.text_b)}