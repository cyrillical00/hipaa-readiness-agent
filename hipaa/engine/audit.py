"""Append-only audit event log."""
import csv
import io

from storage.github_jsonl import append_record, list_records


def log_action(action: str, user: str, cost_usd: float = 0.0,
               metadata: dict | None = None) -> None:
    """Append an audit record for a user."""
    record = {
        "action": action,
        "cost_usd": float(cost_usd or 0.0),
        "metadata": metadata or {},
    }
    append_record(user, "audit", record)


def get_audit_records(user: str, limit: int | None = None) -> list[dict]:
    """Return audit records for a user, newest first."""
    records = list_records(user, "audit")
    records.sort(key=lambda r: r.get("_ts", ""), reverse=True)
    if limit is not None:
        return records[:limit]
    return records


def export_audit_csv(user: str) -> bytes:
    """Return CSV bytes of the audit log for download."""
    records = get_audit_records(user)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "action", "cost_usd", "metadata"])
    for r in records:
        meta = r.get("metadata") or {}
        if isinstance(meta, dict):
            meta_str = "; ".join(f"{k}={v}" for k, v in meta.items())
        else:
            meta_str = str(meta)
        writer.writerow([
            r.get("_ts", ""),
            r.get("action", ""),
            r.get("cost_usd", 0.0),
            meta_str,
        ])
    return buf.getvalue().encode("utf-8")
