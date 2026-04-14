"""
HIPAA control scoring logic.
Required vs Addressable scoring with gap classification.
"""
from typing import Any


REQUIRED_SCORES = {
    "Implemented": 100,
    "Partial": 50,
    "Not Implemented": 0,
    "N/A (Documented)": 100,
}

ADDRESSABLE_SCORES = {
    "Implemented": 100,
    "N/A (Documented)": 100,
    "Partial": 60,
    "Not Implemented": 0,
}

GAP_TIERS = {
    "CRITICAL": {"color": "#DC2626", "bg": "#450a0a"},
    "HIGH": {"color": "#F97316", "bg": "#431407"},
    "MEDIUM": {"color": "#EAB308", "bg": "#422006"},
    "LOW": {"color": "#22C55E", "bg": "#052e16"},
}

READINESS_BANDS = [
    (90, 100, "Ready", "#22C55E"),
    (75, 90, "Nearing Ready", "#F97316"),
    (50, 75, "Partial", "#EAB308"),
    (0, 50, "Not Ready", "#EF4444"),
]


def score_control(control: dict, assessment: dict) -> dict:
    """Score a single control and return score + gap tier."""
    ctrl_id = control["id"]
    status_entry = assessment.get(ctrl_id, {})
    status = status_entry.get("status", "Not Implemented")
    evidence = status_entry.get("evidence", False)
    alt_documented = status_entry.get("alt_documented", None)

    if control["status"] == "Required":
        score = REQUIRED_SCORES.get(status, 0)
        if status == "Not Implemented":
            gap_tier = "CRITICAL"
        elif status == "Partial":
            gap_tier = "HIGH"
        else:
            gap_tier = "LOW" if evidence else "MEDIUM"
    else:
        # Addressable
        if status == "Not Implemented":
            score = ADDRESSABLE_SCORES["Not Implemented"] if not alt_documented else 70
            gap_tier = "HIGH" if not alt_documented else "MEDIUM"
        else:
            score = ADDRESSABLE_SCORES.get(status, 0)
            if status in ("Implemented", "N/A (Documented)"):
                gap_tier = "LOW" if evidence else "MEDIUM"
            else:
                gap_tier = "MEDIUM"

    return {
        "control_id": ctrl_id,
        "score": score,
        "gap_tier": gap_tier,
        "status": status,
        "evidence": evidence,
        "alt_documented": alt_documented,
        "notes": status_entry.get("notes", ""),
    }


def compute_readiness(controls: list[dict], assessment: dict) -> dict:
    """Compute overall and per-category readiness scores."""
    results = [score_control(c, assessment) for c in controls]
    score_map = {r["control_id"]: r for r in results}

    categories = ["Administrative", "Physical", "Technical"]
    cat_scores = {}

    for cat in categories:
        cat_controls = [c for c in controls if c["safeguard"] == cat]
        cat_results = [score_map[c["id"]] for c in cat_controls if c["id"] in score_map]
        if cat_results:
            cat_scores[cat] = sum(r["score"] for r in cat_results) / len(cat_results)
        else:
            cat_scores[cat] = 0

    overall = sum(r["score"] for r in results) / len(results) if results else 0

    critical_gaps = [r for r in results if r["gap_tier"] == "CRITICAL"]
    high_gaps = [r for r in results if r["gap_tier"] == "HIGH"]
    medium_gaps = [r for r in results if r["gap_tier"] == "MEDIUM"]
    low_gaps = [r for r in results if r["gap_tier"] == "LOW"]

    # Quick wins: medium/high gaps with low remediation effort
    control_map = {c["id"]: c for c in controls}
    quick_wins = [
        r for r in (high_gaps + medium_gaps)
        if control_map.get(r["control_id"], {}).get("remediation_effort") == "Low"
    ]

    band_label, band_color = "Not Ready", "#EF4444"
    for lo, hi, label, color in READINESS_BANDS:
        if lo <= overall <= hi:
            band_label, band_color = label, color
            break

    return {
        "overall": round(overall, 1),
        "band_label": band_label,
        "band_color": band_color,
        "category_scores": cat_scores,
        "control_results": score_map,
        "critical_gaps": critical_gaps,
        "high_gaps": high_gaps,
        "medium_gaps": medium_gaps,
        "low_gaps": low_gaps,
        "quick_wins": quick_wins,
        "total_controls": len(results),
        "implemented_count": len([r for r in results if r["status"] in ("Implemented", "N/A (Documented)")]),
        "partial_count": len([r for r in results if r["status"] == "Partial"]),
        "not_implemented_count": len([r for r in results if r["status"] == "Not Implemented"]),
    }


def get_readiness_band(score: float) -> tuple[str, str]:
    for lo, hi, label, color in READINESS_BANDS:
        if lo <= score <= hi:
            return label, color
    return "Not Ready", "#EF4444"
