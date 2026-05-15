# storage

JSONL persistence primitive for per-user state in the HIPAA Readiness Agent.

## Modes

- **Local (default):** files live under `<project_root>/.streamlit/state/{sanitized_email}/{name}.jsonl`.
- **GitHub:** if `HIPAA_STATE_REPO` and `HIPAA_STATE_PAT` are set as Streamlit secrets or env vars, every read and append goes through the GitHub Contents API to the configured repo. Path layout in the repo mirrors local: `{sanitized_email}/{name}.jsonl` at the repo root. API failures raise `storage.github_client.GithubStateError`; there is no silent fallback to local, so misconfigured secrets surface as errors instead of stealth-degraded state.

### Required secrets for GitHub mode

| Key | Value |
|---|---|
| `HIPAA_STATE_REPO` | `owner/repo` of a private repo dedicated to state (e.g. `cyrillical00/hipaa-state-prod`). The default branch must exist (commit at least one file, like a README). |
| `HIPAA_STATE_PAT` | Fine-grained personal access token with **Contents: Read and write** scoped to the state repo. |

The state repo only sees one append commit per write, so it grows linearly with traffic. Squash and archive periodically if storage matters. Never reuse a state repo across deployments that should be isolated.

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
