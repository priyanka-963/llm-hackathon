from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.access import apply_policy
from app.core.analytics import insight_pack
from app.core.data_store import distinct_values


def main() -> None:
    chains = distinct_values("chain_name")
    assert "MARRIOTT" in chains

    filters, policy = apply_policy({"city": "Dubai"}, "marriott")
    assert filters["chain_name"] == "MARRIOTT"
    assert policy["label"] == "Marriott partner"

    pack = insight_pack(filters)
    assert pack["summary"]["bookings"] > 0
    assert pack["risks"]

    print("Smoke test passed")
    print({"chains": chains, "marriott_bookings": pack["summary"]["bookings"], "risk_count": len(pack["risks"])})


if __name__ == "__main__":
    main()
