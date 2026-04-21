from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from app.core.data_store import filter_rows


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def summarize(filters: dict[str, Any]) -> dict[str, Any]:
    rows = filter_rows(filters)
    if not rows:
        return {
            "row_count": 0,
            "message": "No data matched the selected filters.",
            "filters": filters,
        }

    bookings = sum(row["bookings"] for row in rows)
    room_nights = sum(row["room_nights"] for row in rows)
    cancellations = sum(row["cancellations"] for row in rows)
    revenue = sum(row["revenue_usd"] for row in rows)
    weighted_adr = _safe_div(revenue, room_nights)
    avg_occupancy = _safe_div(sum(row["occupancy_pct"] for row in rows), len(rows))
    avg_compset_adr = _safe_div(sum(row["compset_adr_usd"] for row in rows), len(rows))
    avg_sentiment = _safe_div(sum(row["sentiment_score"] for row in rows), len(rows))
    dates = [row["date"] for row in rows]

    return {
        "row_count": len(rows),
        "filters": filters,
        "period": {
            "start": min(dates).isoformat(),
            "end": max(dates).isoformat(),
        },
        "bookings": bookings,
        "room_nights": room_nights,
        "cancellations": cancellations,
        "cancellation_rate_pct": _round(_safe_div(cancellations, bookings) * 100),
        "revenue_usd": _round(revenue),
        "adr_usd": _round(weighted_adr),
        "avg_occupancy_pct": _round(avg_occupancy),
        "avg_compset_adr_usd": _round(avg_compset_adr),
        "adr_gap_vs_compset_usd": _round(weighted_adr - avg_compset_adr),
        "avg_sentiment_score": _round(avg_sentiment),
    }


def group_by_hotel(filters: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in filter_rows(filters):
        grouped[row["hotel_name"]].append(row)

    result = []
    for hotel_name, rows in grouped.items():
        hotel_filters = dict(filters)
        hotel_filters["hotel_name"] = hotel_name
        metrics = summarize(hotel_filters)
        result.append(
            {
                "hotel_name": hotel_name,
                "chain_name": rows[0]["chain_name"],
                "city": rows[0]["city"],
                "revenue_usd": metrics["revenue_usd"],
                "bookings": metrics["bookings"],
                "cancellation_rate_pct": metrics["cancellation_rate_pct"],
                "avg_occupancy_pct": metrics["avg_occupancy_pct"],
                "adr_gap_vs_compset_usd": metrics["adr_gap_vs_compset_usd"],
                "avg_sentiment_score": metrics["avg_sentiment_score"],
            }
        )
    return sorted(result, key=lambda item: item["revenue_usd"], reverse=True)


def detect_risks(filters: dict[str, Any]) -> list[dict[str, Any]]:
    risks = []
    for hotel in group_by_hotel(filters):
        score = 0
        reasons = []
        if hotel["cancellation_rate_pct"] >= 12:
            score += 30
            reasons.append("high cancellation rate")
        if hotel["avg_occupancy_pct"] < 70:
            score += 25
            reasons.append("occupancy below 70%")
        if hotel["adr_gap_vs_compset_usd"] < -15:
            score += 25
            reasons.append("ADR materially below compset")
        if hotel["avg_sentiment_score"] < 4.0:
            score += 20
            reasons.append("guest sentiment is weak")

        if score:
            risks.append(
                {
                    **hotel,
                    "risk_score": min(score, 100),
                    "risk_level": "high" if score >= 60 else "medium",
                    "reasons": reasons,
                    "recommended_action": _recommended_action(reasons),
                }
            )
    return sorted(risks, key=lambda item: item["risk_score"], reverse=True)


def _recommended_action(reasons: list[str]) -> str:
    if "ADR materially below compset" in reasons and "occupancy below 70%" in reasons:
        return "Review price positioning and launch targeted demand stimulation."
    if "high cancellation rate" in reasons:
        return "Audit cancellation sources and rate rules for the affected hotel."
    if "guest sentiment is weak" in reasons:
        return "Prioritize service recovery themes before increasing rates."
    return "Monitor the hotel and compare against the next reporting period."


def trend(filters: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in filter_rows(filters):
        grouped[row["date"]].append(row)

    points = []
    for day, rows in sorted(grouped.items()):
        day_filters = dict(filters)
        day_filters["start_date"] = day.isoformat()
        day_filters["end_date"] = day.isoformat()
        metrics = summarize(day_filters)
        points.append(
            {
                "date": day.isoformat(),
                "revenue_usd": metrics["revenue_usd"],
                "bookings": metrics["bookings"],
                "cancellation_rate_pct": metrics["cancellation_rate_pct"],
                "avg_occupancy_pct": metrics["avg_occupancy_pct"],
            }
        )
    return points


def insight_pack(filters: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": summarize(filters),
        "hotels": group_by_hotel(filters),
        "risks": detect_risks(filters),
        "trend": trend(filters),
    }
