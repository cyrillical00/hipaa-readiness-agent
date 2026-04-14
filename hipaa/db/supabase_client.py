"""
Optional Supabase client for persisting assessments across sessions.
If SUPABASE_URL and SUPABASE_KEY are not configured, all operations are no-ops.
"""
import streamlit as st
import os
import json
from datetime import datetime


def _get_client():
    url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY", ""))
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


def save_assessment(org_name: str, readiness: dict, org_context: dict) -> str | None:
    """Save assessment to Supabase. Returns row ID or None."""
    client = _get_client()
    if not client:
        return None
    try:
        result = client.table("hipaa_assessments").insert({
            "org_name": org_name,
            "overall_score": readiness.get("overall", 0),
            "band_label": readiness.get("band_label", ""),
            "critical_gap_count": len(readiness.get("critical_gaps", [])),
            "high_gap_count": len(readiness.get("high_gaps", [])),
            "org_context": json.dumps(org_context),
            "full_results": json.dumps(readiness),
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        return result.data[0]["id"] if result.data else None
    except Exception:
        return None


def load_recent_assessments(org_name: str, limit: int = 5) -> list[dict]:
    """Load recent assessments for an org."""
    client = _get_client()
    if not client:
        return []
    try:
        result = (
            client.table("hipaa_assessments")
            .select("id, org_name, overall_score, band_label, created_at")
            .eq("org_name", org_name)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []
