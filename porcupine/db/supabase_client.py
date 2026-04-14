"""
Supabase client wrapper.

Handles:
- Authenticated client construction (uses stored session token when available)
- Upsert of Polymarket market cache (markets table)
- Insert of signal run results (signal_runs table, RLS-protected)
- Fetch of recent signal runs for the authenticated user

RLS note: signal_runs has row-level security enabled. The client must be
authenticated (user JWT, not anon key) for inserts and selects to work.
Reads with an unauthenticated client will return 0 rows, not an error.
"""

from __future__ import annotations

import os
from typing import Optional

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")   # anon public key

_client: Optional[Client] = None


def get_client(access_token: Optional[str] = None) -> Client:
    """
    Return a Supabase client.

    If access_token is provided, the client is configured with the user's JWT
    so that RLS policies resolve to the correct user_id. If not provided, the
    client uses the anon key (suitable for public reads only).

    The client is cached for the lifetime of the process. A new token causes
    the cache to be invalidated.
    """
    global _client
    if _client is None or access_token is not None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        if access_token:
            _client.auth.set_session(access_token, "")
    return _client


# ---------------------------------------------------------------------------
# Market cache
# ---------------------------------------------------------------------------

def upsert_markets(markets: list[dict]) -> None:
    """
    Upsert a batch of normalized market dicts into the markets table.

    Uses ON CONFLICT (id) DO UPDATE so repeated fetches don't create duplicates.
    Market dicts must include at minimum: id, question, implied_prob.

    Args:
        markets: List of dicts matching the markets table schema.
    """
    client = get_client()
    rows = []
    for m in markets:
        rows.append({
            "id": m["id"],
            "question": m["question"],
            "implied_prob": m.get("implied_prob"),
            "volume": m.get("volume"),
            "end_date": m.get("end_date"),
        })
    if rows:
        client.table("markets").upsert(rows, on_conflict="id").execute()


def get_market(condition_id: str) -> Optional[dict]:
    """
    Fetch a cached market record from Supabase.
    Returns None if the market is not cached.
    """
    client = get_client()
    resp = client.table("markets").select("*").eq("id", condition_id).limit(1).execute()
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# Signal runs
# ---------------------------------------------------------------------------

def insert_signal_run(
    market_id: str,
    results: list[dict],
    access_token: str,
    user_id: str,
) -> str:
    """
    Insert a signal run into signal_runs (RLS-protected).

    Args:
        market_id:    Polymarket condition_id this run is for.
        results:      List of per-model result dicts from EnsembleResult.to_json_list().
        access_token: User JWT (required for RLS to resolve user_id correctly).
        user_id:      User UUID from Supabase Auth.

    Returns:
        The UUID of the newly created signal_runs row.
    """
    client = get_client(access_token=access_token)
    row = {
        "market_id": market_id,
        "user_id": user_id,
        "results": results,
    }
    resp = client.table("signal_runs").insert(row).execute()
    if resp.data:
        return resp.data[0]["id"]
    raise RuntimeError(f"Supabase insert failed: {resp}")


def get_recent_runs(access_token: str, limit: int = 20) -> list[dict]:
    """
    Fetch the authenticated user's most recent signal runs.

    RLS ensures this only returns rows where user_id = auth.uid().

    Args:
        access_token: User JWT.
        limit:        Max rows to return.

    Returns:
        List of signal_run dicts including market_id, run_at, results.
    """
    client = get_client(access_token=access_token)
    resp = (
        client.table("signal_runs")
        .select("id, market_id, run_at, results")
        .order("run_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []
