"""Generator, validator, and fixer loop for HIPAA roadmap refinement."""
import copy
import json
from engine.claude_client import ClaudeWrapper
from engine.validator import validate_roadmap


_FIXER_SYSTEM_PROMPT = (
    "You are a HIPAA roadmap fixer. You receive a roadmap that failed validation, "
    "plus the validator's complaint list, and you return a corrected roadmap as JSON. "
    "Same structure (executive_summary, overall_risk_tier, phases of 3 with items[], "
    "quick_wins[]). Use only the provided control IDs."
)


class RefineResult:
    """Wraps a refined roadmap with metadata about the refine passes."""

    def __init__(self, roadmap: dict, validation: dict, pass_count: int, history: list[dict]):
        self.roadmap = roadmap
        self.validation = validation
        self.pass_count = pass_count
        self.history = history


def _slim_controls(controls: list[dict]) -> list[dict]:
    slim = []
    for c in controls or []:
        cid = c.get("id")
        if not cid:
            continue
        slim.append({
            "id": cid,
            "standard": c.get("standard", ""),
            "spec": c.get("spec", ""),
        })
    return slim


def _emit(on_pass, pass_num: int, status: str, notes: str) -> None:
    if on_pass is None:
        return
    try:
        on_pass(pass_num, status, notes)
    except Exception:
        pass


def fix_roadmap(
    roadmap: dict,
    validation: dict,
    controls: list[dict],
    critical_gaps: list[dict],
    high_gaps: list[dict],
) -> dict:
    """Single Haiku 4.5 pass that returns a corrected roadmap JSON."""
    slim_controls = _slim_controls(controls)
    missing = validation.get("missing_controls", []) or []
    hallucinated = validation.get("hallucinated_controls", []) or []
    notes = validation.get("notes", "") or ""

    critical_ids = [g.get("control_id") for g in (critical_gaps or []) if g.get("control_id")]
    high_ids = [g.get("control_id") for g in (high_gaps or []) if g.get("control_id")]

    user_prompt = (
        "Original roadmap (failed validation):\n"
        f"{json.dumps(roadmap, indent=2)}\n\n"
        "Validator feedback:\n"
        f"{json.dumps({'missing_controls': missing, 'hallucinated_controls': hallucinated, 'notes': notes}, indent=2)}\n\n"
        "Allowed controls (id, standard, spec only):\n"
        f"{json.dumps(slim_controls, indent=2)}\n\n"
        "Critical gap control ids that MUST appear in the roadmap:\n"
        f"{json.dumps(critical_ids, indent=2)}\n\n"
        "High priority gap control ids:\n"
        f"{json.dumps(high_ids, indent=2)}\n\n"
        "Return a corrected roadmap that:\n"
        "1) Removes any items referencing hallucinated_controls (use real control IDs only).\n"
        "2) Adds at least one item per missing critical control.\n"
        "3) Preserves the structure (executive_summary, overall_risk_tier, "
        "phases[3] with items[], quick_wins[]).\n"
        "4) Returns JSON only, no markdown, no preamble."
    )

    wrapper = ClaudeWrapper(model="claude-haiku-4-5-20251001")
    parsed, _ = wrapper.stream_json(
        system_prompt=_FIXER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=4096,
        progress_label="Fixing roadmap",
    )
    return parsed


def generate_with_refine(
    generator_fn,
    generator_args: tuple,
    controls: list[dict],
    critical_gaps: list[dict],
    high_gaps: list[dict],
    max_passes: int = 3,
    on_pass=None,
) -> RefineResult:
    """Run generator, validate, fix and revalidate up to max_passes times."""
    history: list[dict] = []
    pass_count = 0

    try:
        roadmap = generator_fn(*generator_args)
    except Exception as exc:
        empty_roadmap = {
            "executive_summary": "",
            "overall_risk_tier": "",
            "phases": [],
            "quick_wins": [],
        }
        validation = {
            "status": "fail",
            "missing_controls": [],
            "hallucinated_controls": [],
            "notes": f"Initial generation failed: {exc}",
        }
        history.append({
            "pass": 1,
            "status": "fail",
            "notes": validation["notes"],
            "missing": [],
            "hallucinated": [],
        })
        _emit(on_pass, 1, "fail", validation["notes"])
        return RefineResult(empty_roadmap, validation, 1, history)

    pass_count = 1
    validation = validate_roadmap(roadmap, critical_gaps, high_gaps, controls)
    history.append({
        "pass": pass_count,
        "status": validation.get("status", "fail"),
        "notes": validation.get("notes", ""),
        "missing": list(validation.get("missing_controls", []) or []),
        "hallucinated": list(validation.get("hallucinated_controls", []) or []),
    })
    _emit(on_pass, pass_count, validation.get("status", "fail"), validation.get("notes", ""))

    last_good_roadmap = copy.deepcopy(roadmap)
    last_good_validation = dict(validation)

    while validation.get("status") != "pass" and pass_count < max_passes:
        try:
            fixed_roadmap = fix_roadmap(
                roadmap=last_good_roadmap,
                validation=validation,
                controls=controls,
                critical_gaps=critical_gaps,
                high_gaps=high_gaps,
            )
        except Exception as exc:
            warn_validation = {
                "status": "warn",
                "missing_controls": list(validation.get("missing_controls", []) or []),
                "hallucinated_controls": list(validation.get("hallucinated_controls", []) or []),
                "notes": f"Fixer pass failed; returning last roadmap. Error: {exc}",
            }
            pass_count += 1
            history.append({
                "pass": pass_count,
                "status": "warn",
                "notes": warn_validation["notes"],
                "missing": warn_validation["missing_controls"],
                "hallucinated": warn_validation["hallucinated_controls"],
            })
            _emit(on_pass, pass_count, "warn", warn_validation["notes"])
            return RefineResult(last_good_roadmap, warn_validation, pass_count, history)

        pass_count += 1
        validation = validate_roadmap(fixed_roadmap, critical_gaps, high_gaps, controls)
        history.append({
            "pass": pass_count,
            "status": validation.get("status", "fail"),
            "notes": validation.get("notes", ""),
            "missing": list(validation.get("missing_controls", []) or []),
            "hallucinated": list(validation.get("hallucinated_controls", []) or []),
        })
        _emit(on_pass, pass_count, validation.get("status", "fail"), validation.get("notes", ""))

        last_good_roadmap = copy.deepcopy(fixed_roadmap)
        last_good_validation = dict(validation)

        if validation.get("status") == "pass":
            break

    return RefineResult(last_good_roadmap, last_good_validation, pass_count, history)
