"""Daily per-user spend cap tracker keyed by RBAC role."""
from datetime import datetime, timezone

from storage.github_jsonl import append_record, list_records


ROLE_DAILY_QUOTA_USD = {
    "admin": float("inf"),
    "editor": 10.00,
    "contributor": 2.00,
    "viewer": 0.00,
}


class QuotaExceededError(Exception):
    """Raised when a user has hit their daily spend cap."""


def _today_utc_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def get_today_spend(user: str) -> float:
    """Sum cost_usd of spend records with _ts on today's UTC date."""
    today = _today_utc_date()
    total = 0.0
    for record in list_records(user, "spend"):
        ts = record.get("_ts", "")
        if not ts.startswith(today):
            continue
        try:
            total += float(record.get("cost_usd", 0.0) or 0.0)
        except (TypeError, ValueError):
            continue
    return round(total, 6)


def check_quota(user: str, role: str) -> tuple[bool, float]:
    """Return (allowed, remaining_usd) for the given user and role."""
    quota = ROLE_DAILY_QUOTA_USD.get(role, ROLE_DAILY_QUOTA_USD["viewer"])
    spent = get_today_spend(user)
    if quota == float("inf"):
        return True, float("inf")
    remaining = round(quota - spent, 6)
    return (spent < quota), remaining


def record_spend(user: str, cost_usd: float, model: str = "",
                 call_kind: str = "") -> None:
    """Append a spend record for the user."""
    record = {
        "cost_usd": float(cost_usd or 0.0),
        "model": model or "",
        "call_kind": call_kind or "",
    }
    append_record(user, "spend", record)
