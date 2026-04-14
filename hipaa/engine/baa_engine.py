"""
BAA inventory risk classification logic.
"""
from datetime import datetime, date, timedelta
from typing import Any


RISK_COLORS = {
    "CRITICAL": "#DC2626",
    "HIGH": "#F97316",
    "MEDIUM": "#EAB308",
    "LOW": "#22C55E",
}

RISK_BADGES = {
    "CRITICAL": "🔴 CRITICAL",
    "HIGH": "🟠 HIGH",
    "MEDIUM": "🟡 MEDIUM",
    "LOW": "🟢 LOW",
}


def classify_baa_risk(vendor: dict) -> str:
    """
    Risk classification rules:
    - CRITICAL: ePHI shared + no BAA
    - HIGH: BAA in place but expired, OR no breach clause
    - MEDIUM: BAA complete but sub-BAs not disclosed
    - LOW: Fully compliant
    """
    ephi = vendor.get("ephi_shared", False)
    baa = vendor.get("baa_in_place", False)
    review_date_str = vendor.get("baa_review_date")
    sub_bas = vendor.get("sub_bas_disclosed", False)
    breach_clause = vendor.get("security_incident_clause", False)

    if not ephi:
        return "LOW"

    if ephi and not baa:
        return "CRITICAL"

    # Check expiry
    expired = False
    expiring_soon = False
    if review_date_str:
        try:
            review_date = datetime.strptime(review_date_str, "%Y-%m-%d").date()
            today = date.today()
            if review_date < today:
                expired = True
            elif review_date <= today + timedelta(days=90):
                expiring_soon = True
        except ValueError:
            pass

    if expired:
        return "HIGH"

    if not breach_clause:
        return "HIGH"

    if not sub_bas:
        return "MEDIUM"

    if expiring_soon:
        return "MEDIUM"

    return "LOW"


def enrich_baa_list(baas: list[dict]) -> list[dict]:
    """Add risk_tier and days_until_review to each BAA entry."""
    enriched = []
    today = date.today()
    for baa in baas:
        entry = dict(baa)
        entry["risk_tier"] = classify_baa_risk(baa)
        entry["risk_color"] = RISK_COLORS[entry["risk_tier"]]
        entry["risk_badge"] = RISK_BADGES[entry["risk_tier"]]

        review_str = baa.get("baa_review_date")
        if review_str:
            try:
                review_date = datetime.strptime(review_str, "%Y-%m-%d").date()
                entry["days_until_review"] = (review_date - today).days
            except ValueError:
                entry["days_until_review"] = None
        else:
            entry["days_until_review"] = None

        enriched.append(entry)
    return enriched


def baa_summary(enriched_baas: list[dict]) -> dict:
    """Compute summary metrics for BAA dashboard row."""
    total = len(enriched_baas)
    ephi_vendors = [b for b in enriched_baas if b.get("ephi_shared")]
    missing = len([b for b in ephi_vendors if not b.get("baa_in_place")])
    critical = len([b for b in enriched_baas if b["risk_tier"] == "CRITICAL"])
    high = len([b for b in enriched_baas if b["risk_tier"] == "HIGH"])
    expiring_90d = len([
        b for b in enriched_baas
        if b.get("days_until_review") is not None and 0 <= b["days_until_review"] <= 90
    ])
    expired = len([
        b for b in enriched_baas
        if b.get("days_until_review") is not None and b["days_until_review"] < 0
    ])

    return {
        "total": total,
        "ephi_vendors": len(ephi_vendors),
        "missing_baas": missing,
        "expiring_90d": expiring_90d,
        "expired": expired,
        "critical": critical,
        "high": high,
        "compliance_rate": round(
            (len(ephi_vendors) - missing) / len(ephi_vendors) * 100 if ephi_vendors else 100, 1
        ),
    }
