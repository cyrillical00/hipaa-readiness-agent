"""
Polymarket CLOB API ingestion wrapper.

Uses py-clob-client in read-only mode (no wallet/API key required for public data).
Returns normalized Market objects for use across the CLI and signal engine.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from dotenv import load_dotenv

load_dotenv()

CLOB_HOST = os.getenv("POLYMARKET_CLOB_HOST", "https://clob.polymarket.com")


@dataclass
class Market:
    condition_id: str
    question: str
    implied_prob: Optional[float]   # YES token price ≈ probability
    volume: Optional[float]
    end_date: Optional[str]
    active: bool = True
    raw: dict = None                # full API payload for debugging

    def delta(self, estimate: float) -> float:
        """Signal delta: LLM estimate minus market-implied probability."""
        if self.implied_prob is None:
            return 0.0
        return estimate - self.implied_prob


def _build_client() -> ClobClient:
    """Build a read-only ClobClient (no credentials required for public endpoints)."""
    return ClobClient(CLOB_HOST)


def _extract_yes_price(token_data: list[dict]) -> Optional[float]:
    """
    Pull the YES token price from token metadata.
    Polymarket returns two tokens per market: YES and NO.
    The YES price is the market-implied probability.
    """
    if not token_data:
        return None
    for token in token_data:
        outcome = (token.get("outcome") or "").upper()
        if outcome == "YES":
            price = token.get("price")
            if price is not None:
                try:
                    return float(price)
                except (TypeError, ValueError):
                    return None
    # Fallback: first token price if outcome labels aren't standard
    try:
        return float(token_data[0].get("price") or 0)
    except (TypeError, ValueError):
        return None


def _normalize(raw: dict) -> Market:
    """Convert a raw Polymarket market dict into a normalized Market object."""
    condition_id = raw.get("condition_id") or raw.get("id") or ""
    question = raw.get("question") or raw.get("description") or "(no question)"
    tokens = raw.get("tokens") or []
    implied_prob = _extract_yes_price(tokens)

    # Volume: sum of all token volumes or top-level volume
    volume = raw.get("volume")
    if volume is None:
        volume = raw.get("volume_num")
    try:
        volume = float(volume) if volume is not None else None
    except (TypeError, ValueError):
        volume = None

    end_date = raw.get("end_date_iso") or raw.get("end_date") or raw.get("game_start_time")
    active = raw.get("active", True)

    return Market(
        condition_id=condition_id,
        question=question,
        implied_prob=implied_prob,
        volume=volume,
        end_date=end_date,
        active=bool(active),
        raw=raw,
    )


def fetch_markets(limit: int = 50, only_active: bool = True) -> list[Market]:
    """
    Fetch the top N active markets from Polymarket, sorted by volume descending.

    Args:
        limit: Max number of markets to return after filtering.
        only_active: If True, skip resolved/closed markets.

    Returns:
        List of normalized Market objects.
    """
    client = _build_client()

    markets: list[Market] = []
    next_cursor = ""

    # Page through results until we have enough or exhaust the feed
    while len(markets) < limit * 3:  # over-fetch to account for filtering
        try:
            if next_cursor:
                resp = client.get_markets(next_cursor=next_cursor)
            else:
                resp = client.get_markets()
        except Exception as exc:
            raise RuntimeError(f"Polymarket API error: {exc}") from exc

        raw_list = resp.get("data") or []
        for raw in raw_list:
            m = _normalize(raw)
            if only_active and not m.active:
                continue
            if m.implied_prob is None:
                continue  # skip markets with no price data
            markets.append(m)

        next_cursor = resp.get("next_cursor") or ""
        if not next_cursor or next_cursor == "LTE=":
            break  # LTE= is Polymarket's sentinel for "no more pages"

    # Sort by volume descending, put None volumes at the end
    markets.sort(key=lambda m: m.volume or 0, reverse=True)
    return markets[:limit]


def fetch_market(condition_id: str) -> Market:
    """
    Fetch a single market by condition_id.

    Args:
        condition_id: Polymarket condition ID (hex string).

    Returns:
        Normalized Market object.

    Raises:
        ValueError: If the market is not found.
    """
    client = _build_client()
    try:
        raw = client.get_market(condition_id)
    except Exception as exc:
        raise RuntimeError(f"Polymarket API error fetching {condition_id}: {exc}") from exc

    if not raw:
        raise ValueError(f"Market not found: {condition_id}")

    return _normalize(raw)
