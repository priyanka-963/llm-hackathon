from __future__ import annotations

from datetime import date
from functools import lru_cache
import csv
from typing import Any

from app.core.settings import get_settings


NUMERIC_FIELDS = {
    "bookings": int,
    "room_nights": int,
    "cancellations": int,
    "revenue_usd": float,
    "adr_usd": float,
    "occupancy_pct": float,
    "compset_adr_usd": float,
    "sentiment_score": float,
}


def _normalize_row(row: dict[str, str]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        clean_value = (value or "").strip()
        if key == "date":
            normalized[key] = date.fromisoformat(clean_value)
        elif key in NUMERIC_FIELDS:
            normalized[key] = NUMERIC_FIELDS[key](clean_value or 0)
        else:
            normalized[key] = clean_value
    return normalized


@lru_cache
def load_rows() -> list[dict[str, Any]]:
    path = get_settings().resolved_data_path
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [_normalize_row(row) for row in reader]


def distinct_values(field: str) -> list[str]:
    return sorted({str(row[field]) for row in load_rows() if row.get(field)})


def filter_rows(filters: dict[str, Any]) -> list[dict[str, Any]]:
    rows = load_rows()
    chain = str(filters.get("chain_name") or "").strip().upper()
    city = str(filters.get("city") or "").strip().lower()
    hotel = str(filters.get("hotel_name") or "").strip().lower()
    start_date = filters.get("start_date")
    end_date = filters.get("end_date")

    if isinstance(start_date, str) and start_date:
        start_date = date.fromisoformat(start_date)
    if isinstance(end_date, str) and end_date:
        end_date = date.fromisoformat(end_date)

    result = []
    for row in rows:
        if chain and row["chain_name"].upper() != chain:
            continue
        if city and row["city"].lower() != city:
            continue
        if hotel and row["hotel_name"].lower() != hotel:
            continue
        if start_date and row["date"] < start_date:
            continue
        if end_date and row["date"] > end_date:
            continue
        result.append(row)
    return result
