# storage

JSONL persistence primitive for per-user state in the HIPAA Readiness Agent.

## Modes

- **Local (default):** files live under `<project_root>/.streamlit/state/{sanitized_email}/{name}.jsonl`.
- **GitHub (stub):** if `HIPAA_STATE_REPO` and `HIPAA_STATE_PAT` are set as Streamlit secrets or env vars, `get_storage_mode()` reports `github`. The actual GitHub Contents API path is not wired up yet; reads and writes silently fall through to local mode and print a one-line warning. See the `# TODO Phase 6.5 follow-up` markers in `github_jsonl.py`.

## File layout

```
.streamlit/state/
  user_at_example_dot_com/
    audit.jsonl
    spend.jsonl
    assessments.jsonl
    roadmap_state.jsonl
```

## Email sanitization

`_email_to_dir(email)` lowercases, strips, then replaces `@` with `_at_` and `.` with `_dot_`. So `User@Example.com` becomes `user_at_example_dot_com`.

## Schema notes

Every appended record gets an `_ts` ISO 8601 UTC timestamp if the caller did not supply one. Beyond that, schemas are owned by the calling module (`engine/audit.py`, `engine/spend_quota.py`, etc.).
