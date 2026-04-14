"""
SOC2 → HIPAA overlap analysis engine.
Computes overlap coverage based on org's SOC2 status.
"""
import json
import os
from typing import Any


def load_crosswalk() -> list[dict]:
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "data", "soc2_hipaa_crosswalk.json")
    with open(path) as f:
        return json.load(f)


def compute_overlap(crosswalk: list[dict], soc2_status: str) -> dict:
    """
    soc2_status: "None" | "Type I in progress" | "Type I Complete" | "Type II Complete"
    Returns per-control overlap analysis and aggregate stats.
    """
    soc2_done = soc2_status in ("Type I Complete", "Type II Complete")
    soc2_full = soc2_status == "Type II Complete"

    results = []
    for item in crosswalk:
        overlap = item["overlap_type"]
        criteria = item["soc2_criteria"]

        if not criteria:
            effective_overlap = "None"
        elif not soc2_done:
            # SOC2 not complete — show as Potential
            effective_overlap = f"Potential ({overlap})" if overlap != "None" else "None"
        elif soc2_full:
            effective_overlap = overlap
        else:
            # Type I done — partial credit: Full → Partial, Partial → Partial
            effective_overlap = "Partial" if overlap in ("Full", "Partial") else "None"

        results.append({
            "hipaa_id": item["hipaa_id"],
            "hipaa_spec": item["hipaa_spec"],
            "soc2_criteria": criteria,
            "overlap_type": overlap,
            "effective_overlap": effective_overlap,
            "notes": item["notes"],
        })

    # Stats
    total = len(results)
    full = len([r for r in results if r["effective_overlap"] == "Full"])
    partial = len([r for r in results if "Partial" in r["effective_overlap"]])
    none_count = len([r for r in results if r["effective_overlap"] == "None"])
    potential = len([r for r in results if "Potential" in r["effective_overlap"]])

    # By safeguard
    safeguards = {
        "Administrative": [r for r in results if r["hipaa_id"].startswith("ADM")],
        "Physical": [r for r in results if r["hipaa_id"].startswith("PHY")],
        "Technical": [r for r in results if r["hipaa_id"].startswith("TEC")],
    }

    cat_stats = {}
    for cat, items in safeguards.items():
        cat_stats[cat] = {
            "full": len([i for i in items if i["effective_overlap"] == "Full"]),
            "partial": len([i for i in items if "Partial" in i["effective_overlap"]]),
            "none": len([i for i in items if i["effective_overlap"] == "None"]),
            "potential": len([i for i in items if "Potential" in i["effective_overlap"]]),
            "total": len(items),
        }

    coverage_pct = round((full + partial * 0.5) / total * 100, 1) if total else 0

    return {
        "items": results,
        "total": total,
        "full_overlap": full,
        "partial_overlap": partial,
        "no_overlap": none_count,
        "potential": potential,
        "coverage_pct": coverage_pct,
        "category_stats": cat_stats,
        "soc2_status": soc2_status,
        "soc2_done": soc2_done,
    }
