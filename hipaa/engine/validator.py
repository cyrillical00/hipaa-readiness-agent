"""Independent Claude pass that fact-checks a generated HIPAA roadmap."""
import json
from engine.claude_client import ClaudeWrapper

_VALIDATOR_SYSTEM_PROMPT = (
    "You are a HIPAA roadmap validator. You receive a deterministic pre-check result "
    "and roadmap excerpt. Confirm or downgrade the status, write a 1-2 sentence note. "
    "Reply JSON only with keys: status, notes."
)


def _collect_roadmap_control_ids(roadmap: dict) -> set[str]:
    found: set[str] = set()
    for phase in roadmap.get("phases", []) or []:
        for item in phase.get("items", []) or []:
            cid = item.get("control_id")
            if cid:
                found.add(cid)
    for qw in roadmap.get("quick_wins", []) or []:
        cid = qw.get("control_id")
        if cid:
            found.add(cid)
    return found


def validate_roadmap(
    roadmap: dict,
    critical_gaps: list[dict],
    high_gaps: list[dict],
    controls: list[dict],
) -> dict:
    valid_control_ids = {c.get("id") for c in controls if c.get("id")}
    roadmap_ids = _collect_roadmap_control_ids(roadmap)

    hallucinated = sorted(roadmap_ids - valid_control_ids)
    critical_ids = {g.get("control_id") for g in critical_gaps if g.get("control_id")}
    missing = sorted(critical_ids - roadmap_ids)

    if hallucinated:
        baseline_status = "fail"
    elif missing:
        baseline_status = "warn"
    else:
        baseline_status = "pass"

    excerpt = {
        "executive_summary": roadmap.get("executive_summary", ""),
        "overall_risk_tier": roadmap.get("overall_risk_tier", ""),
        "phase_count": len(roadmap.get("phases", []) or []),
        "total_items": sum(len(p.get("items", []) or []) for p in roadmap.get("phases", []) or []),
    }

    user_prompt = (
        "Pre-check result:\n"
        f"{json.dumps({'baseline_status': baseline_status, 'hallucinated_controls': hallucinated, 'missing_critical_controls': missing}, indent=2)}\n\n"
        "Roadmap excerpt:\n"
        f"{json.dumps(excerpt, indent=2)}\n\n"
        "Rules:\n"
        "1. You may keep the baseline status or downgrade it (pass to warn or fail; warn to fail). "
        "You may NOT upgrade.\n"
        "2. Write a 1-2 sentence note summarizing the validation result.\n"
        "3. Reply JSON only: {\"status\": \"pass|warn|fail\", \"notes\": \"...\"}"
    )

    severity_rank = {"pass": 0, "warn": 1, "fail": 2}
    final_status = baseline_status
    notes = ""

    try:
        wrapper = ClaudeWrapper(model="claude-haiku-4-5-20251001")
        parsed, _ = wrapper.stream_json(
            system_prompt=_VALIDATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=1024,
            progress_label="Validating",
        )
        claude_status = str(parsed.get("status", baseline_status)).lower()
        if claude_status not in severity_rank:
            claude_status = baseline_status
        if severity_rank[claude_status] >= severity_rank[baseline_status]:
            final_status = claude_status
        notes = str(parsed.get("notes", "")).strip()
    except Exception as exc:
        notes = f"Validator LLM call failed; using deterministic baseline. Error: {exc}"

    if not notes:
        if final_status == "pass":
            notes = "Roadmap covers all critical gaps and references only known controls."
        elif final_status == "warn":
            notes = (
                f"Roadmap is missing {len(missing)} critical control(s); "
                "review and add coverage."
            )
        else:
            notes = (
                f"Roadmap references {len(hallucinated)} unknown control id(s); "
                "regenerate or correct before use."
            )

    return {
        "status": final_status,
        "missing_controls": missing,
        "hallucinated_controls": hallucinated,
        "notes": notes,
    }
