from typing import Any


PROFILE_POLICIES = {
    "internal": {
        "label": "Internal analyst",
        "scope": {},
        "can_compare_chains": True,
    },
    "marriott": {
        "label": "Marriott partner",
        "scope": {"chain_name": "MARRIOTT"},
        "can_compare_chains": False,
    },
    "hilton": {
        "label": "Hilton partner",
        "scope": {"chain_name": "HILTON"},
        "can_compare_chains": False,
    },
}


def get_policy(profile: str | None) -> dict[str, Any]:
    normalized = (profile or "internal").strip().lower()
    return PROFILE_POLICIES.get(normalized, PROFILE_POLICIES["internal"])


def apply_policy(filters: dict[str, Any], profile: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    policy = get_policy(profile)
    scoped_filters = dict(filters or {})
    for key, value in policy.get("scope", {}).items():
        requested = scoped_filters.get(key)
        if requested and str(requested).strip().upper() != str(value).strip().upper():
            raise PermissionError(f"This profile can only query {value} data.")
        scoped_filters[key] = value
    return scoped_filters, policy

