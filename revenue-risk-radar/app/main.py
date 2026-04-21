from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.core.access import apply_policy, get_policy
from app.core.analytics import insight_pack
from app.core.data_store import distinct_values
from app.core.llm import LLMClient, build_business_prompt
from app.core.settings import get_settings


settings = get_settings()
llm_client = LLMClient()

app = FastAPI(title=settings.app_name)


class FilterRequest(BaseModel):
    profile: str = Field(default="internal", description="internal, marriott, or hilton")
    chain_name: Optional[str] = None
    city: Optional[str] = None
    hotel_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ChatRequest(FilterRequest):
    question: str


def _filters_from_request(req: FilterRequest) -> tuple[dict[str, Any], dict[str, Any]]:
    filters = {
        "chain_name": req.chain_name,
        "city": req.city,
        "hotel_name": req.hotel_name,
        "start_date": req.start_date,
        "end_date": req.end_date,
    }
    filters = {key: value for key, value in filters.items() if value not in (None, "")}
    try:
        return apply_policy(filters, req.profile)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.get("/")
def home() -> HTMLResponse:
    html_path = Path(__file__).resolve().parent / "static" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "llm_provider": llm_client.provider,
        "llm_configured": llm_client.configured(),
    }


@app.get("/api/options")
def options() -> dict[str, list[str]]:
    return {
        "profiles": ["internal", "marriott", "hilton"],
        "chains": distinct_values("chain_name"),
        "cities": distinct_values("city"),
        "hotels": distinct_values("hotel_name"),
    }


@app.post("/api/insights")
def insights(req: FilterRequest) -> dict[str, Any]:
    filters, policy = _filters_from_request(req)
    return {
        "policy": policy,
        "filters": filters,
        "insights": insight_pack(filters),
    }


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict[str, Any]:
    filters, policy = _filters_from_request(req)
    pack = insight_pack(filters)
    system_prompt, user_prompt = build_business_prompt(req.question, pack, policy)
    try:
        answer = llm_client.complete(system_prompt, user_prompt)
    except Exception as exc:
        answer = (
            "The analytics were computed successfully, but the LLM call failed. "
            f"Provider error: {exc}"
        )
    return {
        "answer": answer,
        "provider": llm_client.provider,
        "llm_configured": llm_client.configured(),
        "policy": policy,
        "filters": filters,
        "insights": pack,
    }


@app.get("/api/profile/{profile}")
def profile(profile: str) -> dict[str, Any]:
    return get_policy(profile)
