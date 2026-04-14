"""CSV / JSON upload fallback connector."""
import pandas as pd
import json
import io
from typing import Any


EXPECTED_CSV_COLUMNS = [
    "control_id", "status", "evidence", "notes", "alt_control_documented"
]

VALID_STATUSES = ["Implemented", "Partial", "Not Implemented", "N/A (Documented)"]


def parse_csv_upload(file_content: bytes) -> tuple[dict, list[str]]:
    """
    Parse CSV upload into assessment dict.
    Returns (assessment_dict, errors).
    """
    errors = []
    assessment = {}

    try:
        df = pd.read_csv(io.BytesIO(file_content))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        missing = [c for c in ["control_id", "status"] if c not in df.columns]
        if missing:
            errors.append(f"Missing required columns: {', '.join(missing)}")
            return assessment, errors

        for _, row in df.iterrows():
            ctrl_id = str(row.get("control_id", "")).strip()
            status = str(row.get("status", "Not Implemented")).strip()

            if not ctrl_id:
                continue

            if status not in VALID_STATUSES:
                errors.append(f"Row {ctrl_id}: Invalid status '{status}'. Using 'Not Implemented'.")
                status = "Not Implemented"

            evidence_raw = row.get("evidence", False)
            evidence = str(evidence_raw).lower() in ("true", "yes", "1") if pd.notna(evidence_raw) else False

            alt_raw = row.get("alt_control_documented", None)
            alt = None
            if pd.notna(alt_raw):
                alt = str(alt_raw).lower() in ("true", "yes", "1")

            assessment[ctrl_id] = {
                "status": status,
                "evidence": evidence,
                "alt_documented": alt,
                "notes": str(row.get("notes", "")) if pd.notna(row.get("notes", "")) else "",
            }

    except Exception as e:
        errors.append(f"Parse error: {str(e)}")

    return assessment, errors


def generate_csv_template(controls: list[dict]) -> str:
    """Generate a blank CSV template for manual upload."""
    rows = ["control_id,status,evidence,notes,alt_control_documented"]
    for c in controls:
        rows.append(f"{c['id']},Not Implemented,false,,")
    return "\n".join(rows)
