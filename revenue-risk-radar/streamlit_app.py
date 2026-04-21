from __future__ import annotations

import os
from typing import Any

import streamlit as st


def _apply_streamlit_secrets() -> None:
    keys = (
        "LLM_PROVIDER",
        "GROQ_API_KEY",
        "GROQ_MODEL",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "DATA_PATH",
    )
    try:
        for key in keys:
            if key in st.secrets and not os.getenv(key):
                os.environ[key] = str(st.secrets[key])
    except Exception:
        return


_apply_streamlit_secrets()

from app.core.access import apply_policy
from app.core.analytics import insight_pack
from app.core.data_store import distinct_values
from app.core.llm import LLMClient, build_business_prompt


st.set_page_config(
    page_title="Hotel Revenue Risk Radar",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; }
      div[data-testid="stMetric"] {
        background: #fff8e8;
        border: 1px solid #eadfc7;
        border-radius: 18px;
        padding: 18px;
      }
      .risk-card {
        background: #fff8e8;
        border: 1px solid #eadfc7;
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 12px;
      }
      .risk-badge {
        display: inline-block;
        border-radius: 999px;
        padding: 4px 10px;
        background: rgba(180,83,44,.14);
        color: #9a3f22;
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
      }
      .muted { color: #756f62; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _money(value: Any, decimals: int = 0) -> str:
    return f"${float(value or 0):,.{decimals}f}"


def _pct(value: Any) -> str:
    return f"{float(value or 0):.1f}%"


def _build_filters(profile: str, chain: str | None, city: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    filters = {
        "chain_name": chain or None,
        "city": city or None,
    }
    filters = {key: value for key, value in filters.items() if value}
    return apply_policy(filters, profile)


def _render_risk_card(risk: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="risk-card">
          <span class="risk-badge">{risk["risk_level"]} risk {risk["risk_score"]}</span>
          <h4>{risk["hotel_name"]}</h4>
          <div class="muted">{", ".join(risk["reasons"])}</div>
          <div>{risk["recommended_action"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


llm_client = LLMClient()

st.title("Hotel Revenue Risk Radar")
st.caption("Deployed AI Copilot")

with st.sidebar:
    st.header("Access Scope")
    profile = st.selectbox(
        "Viewer profile",
        options=["internal", "marriott", "hilton"],
        format_func=lambda value: {
            "internal": "Internal analyst",
            "marriott": "Marriott partner",
            "hilton": "Hilton partner",
        }[value],
    )

    chain_options = [""] + distinct_values("chain_name")
    city_options = [""] + distinct_values("city")

    default_chain = ""
    if profile == "marriott":
        default_chain = "MARRIOTT"
    elif profile == "hilton":
        default_chain = "HILTON"

    chain = st.selectbox(
        "Chain filter",
        options=chain_options,
        index=chain_options.index(default_chain) if default_chain in chain_options else 0,
        disabled=bool(default_chain),
        format_func=lambda value: value or "All chains",
    )
    city = st.selectbox("City", options=city_options, format_func=lambda value: value or "All cities")

try:
    filters, policy = _build_filters(profile, chain, city)
except PermissionError as exc:
    st.error(str(exc))
    st.stop()

pack = insight_pack(filters)
summary = pack["summary"]

provider_label = llm_client.provider if llm_client.configured() else "AI provider required"
st.info(f"AI status: {provider_label}. Current scope: {policy['label']}.")

st.subheader("Ask the AI copilot")
question = st.text_area(
    "Ask Copilot",
    value="Which hotel needs attention and what should we do next?",
    label_visibility="collapsed",
)

if st.button("Ask Copilot", type="primary"):
    system_prompt, user_prompt = build_business_prompt(question, pack, policy)
    try:
        st.write(llm_client.complete(system_prompt, user_prompt))
    except Exception as exc:
        st.error(f"The analytics were computed successfully, but the LLM call failed: {exc}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Revenue", _money(summary.get("revenue_usd")))
col2.metric("Bookings", f"{int(summary.get('bookings', 0)):,.0f}")
col3.metric("Cancellation Rate", _pct(summary.get("cancellation_rate_pct")))
col4.metric("ADR Gap", _money(summary.get("adr_gap_vs_compset_usd")))

left, right = st.columns([1, 1])

with left:
    st.subheader("Risk Watchlist")
    risks = pack["risks"]
    if risks:
        for risk in risks[:8]:
            _render_risk_card(risk)
    else:
        st.success("No material risks found for this scope.")

with right:
    st.subheader("Hotel Performance")
    hotels = pack["hotels"]
    if hotels:
        st.dataframe(
            hotels,
            hide_index=True,
            use_container_width=True,
            column_order=[
                "hotel_name",
                "chain_name",
                "city",
                "revenue_usd",
                "bookings",
                "cancellation_rate_pct",
                "avg_occupancy_pct",
                "adr_gap_vs_compset_usd",
            ],
        )
    else:
        st.warning("No hotel records matched this scope.")
