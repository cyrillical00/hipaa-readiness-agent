"""QA regression harness for the HIPAA Readiness Agent."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
CASES_DIR = ROOT / "cases"
REPLAYS_DIR = ROOT / "replays"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_controls() -> list[dict]:
    controls_path = PROJECT_ROOT / "data" / "hipaa_controls.json"
    with open(controls_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_cases(filter_str: str | None = None) -> list[dict]:
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        case_id = path.stem
        data["_case_id"] = case_id
        data["_path"] = str(path)
        if filter_str and filter_str.lower() not in case_id.lower():
            continue
        cases.append(data)
    return cases


def assert_shape(name: str, payload: dict, shape: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []

    for key in shape.get("must_have_keys", []):
        if key not in payload:
            failures.append(f"{name}: missing required key '{key}'")

    if "phases_count" in shape:
        phases = payload.get("phases", []) or []
        if len(phases) != shape["phases_count"]:
            failures.append(
                f"{name}: expected {shape['phases_count']} phases, got {len(phases)}"
            )

    if "min_items_per_phase" in shape:
        for idx, phase in enumerate(payload.get("phases", []) or []):
            items = phase.get("items", []) or []
            if len(items) < shape["min_items_per_phase"]:
                failures.append(
                    f"{name}: phase {idx + 1} has {len(items)} items, "
                    f"need at least {shape['min_items_per_phase']}"
                )

    if "must_address_control_ids" in shape:
        addressed: set[str] = set()
        for phase in payload.get("phases", []) or []:
            for item in phase.get("items", []) or []:
                cid = item.get("control_id")
                if cid:
                    addressed.add(cid)
        for required_cid in shape["must_address_control_ids"]:
            if required_cid not in addressed:
                failures.append(
                    f"{name}: roadmap does not address required control '{required_cid}'"
                )

    if "min_critical_gaps" in shape:
        crit = payload.get("critical_gaps", []) or []
        if len(crit) < shape["min_critical_gaps"]:
            failures.append(
                f"{name}: expected at least {shape['min_critical_gaps']} critical_gaps, "
                f"got {len(crit)}"
            )

    if "risk_tier_in" in shape:
        actual = payload.get("overall_risk_tier", "")
        if actual not in shape["risk_tier_in"]:
            failures.append(
                f"{name}: overall_risk_tier '{actual}' not in {shape['risk_tier_in']}"
            )

    return (len(failures) == 0, failures)


def replay_paths(case_id: str) -> tuple[Path, Path]:
    return (
        REPLAYS_DIR / f"{case_id}_score.json",
        REPLAYS_DIR / f"{case_id}_roadmap.json",
    )


def run_live(case: dict, controls: list[dict]) -> tuple[dict, dict]:
    from engine import roadmap_generator

    score = roadmap_generator.score_assessment_with_claude(
        control_statuses=case["control_statuses"],
        controls=controls,
        connector_findings=case.get("connector_findings", {}),
        org_context=case["org_context"],
    )
    roadmap = roadmap_generator.generate_roadmap(
        control_results=case["control_results"],
        controls=controls,
        baa_summary=case["baa_summary"],
        overlap_analysis=case["overlap_analysis"],
        org_context=case["org_context"],
    )

    score_path, roadmap_path = replay_paths(case["_case_id"])
    REPLAYS_DIR.mkdir(parents=True, exist_ok=True)
    score_path.write_text(json.dumps(score, indent=2), encoding="utf-8")
    roadmap_path.write_text(json.dumps(roadmap, indent=2), encoding="utf-8")
    return score, roadmap


def run_replay(case: dict) -> tuple[dict | None, dict | None, str]:
    score_path, roadmap_path = replay_paths(case["_case_id"])
    if not score_path.exists() or not roadmap_path.exists():
        return None, None, (
            f"missing replay; run 'python qa/runner.py --live --case {case['_case_id']}' first"
        )
    score = json.loads(score_path.read_text(encoding="utf-8"))
    roadmap = json.loads(roadmap_path.read_text(encoding="utf-8"))
    return score, roadmap, ""


def evaluate_case(case: dict, score: dict, roadmap: dict, controls: list[dict]) -> tuple[bool, list[str]]:
    from engine import validator

    failures: list[str] = []

    score_ok, score_fails = assert_shape("score", score, case.get("expected_score_shape", {}))
    if not score_ok:
        failures.extend(score_fails)

    roadmap_ok, roadmap_fails = assert_shape("roadmap", roadmap, case.get("expected_roadmap_shape", {}))
    if not roadmap_ok:
        failures.extend(roadmap_fails)

    try:
        v = validator.validate_roadmap(
            roadmap=roadmap,
            critical_gaps=case["control_results"].get("critical_gaps", []),
            high_gaps=case["control_results"].get("high_gaps", []),
            controls=controls,
        )
        if v.get("status") == "fail":
            failures.append(
                f"validator: status=fail, hallucinated={v.get('hallucinated_controls')}, "
                f"missing={v.get('missing_controls')}"
            )
    except Exception as exc:
        failures.append(f"validator raised exception: {exc}")

    return (len(failures) == 0, failures)


def main() -> int:
    parser = argparse.ArgumentParser(description="HIPAA QA regression harness")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--replay", action="store_true", help="Use cached replays (default)")
    mode.add_argument("--live", action="store_true", help="Hit the Anthropic API and refresh replays")
    parser.add_argument("--case", type=str, default=None, help="Substring filter on case id")
    args = parser.parse_args()

    is_live = bool(args.live)

    cases = load_cases(args.case)
    if not cases:
        print("No cases matched.")
        return 1

    controls = load_controls()
    print(f"Loaded {len(cases)} case(s), {len(controls)} controls.")
    print(f"Mode: {'LIVE (calling Anthropic)' if is_live else 'REPLAY (cached)'}")
    print("")

    pass_count = 0
    fail_count = 0
    skip_count = 0

    for case in cases:
        case_id = case["_case_id"]
        label = f"[{case_id}] {case['name']}"
        try:
            if is_live:
                score, roadmap = run_live(case, controls)
                ok, failures = evaluate_case(case, score, roadmap, controls)
            else:
                score, roadmap, skip_reason = run_replay(case)
                if skip_reason:
                    print(f"SKIP {label}")
                    print(f"     hint: {skip_reason}")
                    skip_count += 1
                    continue
                ok, failures = evaluate_case(case, score, roadmap, controls)
        except Exception as exc:
            print(f"FAIL {label}")
            print(f"     exception: {exc}")
            fail_count += 1
            continue

        if ok:
            print(f"PASS {label}")
            pass_count += 1
        else:
            print(f"FAIL {label}")
            for line in failures:
                print(f"     {line}")
            fail_count += 1

    print("")
    print(f"Summary: {pass_count} passed, {fail_count} failed, {skip_count} skipped")

    if is_live:
        try:
            from engine.claude_client import get_session_usage
            usage = get_session_usage()
            print(
                f"Total cost: ${usage.get('total_cost_usd', 0):.4f} "
                f"across {usage.get('call_count', 0)} call(s)"
            )
        except Exception as exc:
            print(f"Could not read session usage: {exc}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
