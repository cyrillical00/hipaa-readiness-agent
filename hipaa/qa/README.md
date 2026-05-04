# QA Regression Harness

Self contained regression harness for the two Claude calls in `engine/roadmap_generator.py`:

1. `score_assessment_with_claude` (gap analysis JSON)
2. `generate_roadmap` (3 phase remediation plan JSON)

Plus a final `engine.validator.validate_roadmap` pass on every roadmap.

## Layout

```
qa/
  cases/      JSON fixtures, one per scenario
  replays/    Cached Claude responses (created on first --live run)
  runner.py   CLI entrypoint
```

## Run modes

`python qa/runner.py --replay`

Default. Reads cached responses from `qa/replays/`. Fast, free, deterministic.
A case with no replay file is marked SKIPPED with a hint.

`python qa/runner.py --live`

Hits the Anthropic API for every case, saves the parsed JSON to `qa/replays/`,
then runs the same assertions. Use this when prompts or the model change.

`python qa/runner.py --case meridian`

Substring filter on the case id (file stem). Combine with `--live` or `--replay`.

## Adding a fixture

Drop a new JSON file in `qa/cases/` matching the schema of `case_meridian_demo.json`.
Required top level keys: `name`, `description`, `org_context`, `control_statuses`,
`connector_findings`, `control_results`, `baa_summary`, `overlap_analysis`,
`expected_score_shape`, `expected_roadmap_shape`.

`expected_*_shape` drives the assertions. See the meridian fixture for the full
list of supported assertion keys (`must_have_keys`, `phases_count`,
`min_items_per_phase`, `must_address_control_ids`, `min_critical_gaps`,
`risk_tier_in`).

## Cost estimate per `--live` run

5 cases x 2 calls x roughly 3000 input plus 2000 output tokens on
`claude-sonnet-4-6` works out to about $0.50 per full live pass, with the
validator (Haiku) adding a few cents on top.

## Exit codes

`0` if every selected case passes. `1` if any case fails.
