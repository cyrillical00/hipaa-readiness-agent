"""Centralized Anthropic client wrapper with prompt caching and usage tracking."""
import json
import os
import anthropic

try:
    import streamlit as st
    _HAS_ST = True
except Exception:
    st = None
    _HAS_ST = False

_FALLBACK_USAGE_LOG: list[dict] = []

PRICING = {
    "claude-sonnet-4-6": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.30,
    },
    "claude-haiku-4-5-20251001": {
        "input": 1.0,
        "output": 5.0,
        "cache_write": 1.25,
        "cache_read": 0.10,
    },
}


def _resolve_api_key() -> str:
    api_key = ""
    if _HAS_ST:
        try:
            api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            api_key = ""
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured in secrets or environment.")
    return api_key


def _get_usage_log() -> list[dict]:
    if _HAS_ST:
        try:
            if "claude_usage_log" not in st.session_state:
                st.session_state["claude_usage_log"] = []
            return st.session_state["claude_usage_log"]
        except Exception:
            return _FALLBACK_USAGE_LOG
    return _FALLBACK_USAGE_LOG


def _calculate_cost(model: str, input_tokens: int, output_tokens: int,
                    cache_creation: int, cache_read: int) -> float:
    rates = PRICING.get(model, PRICING["claude-sonnet-4-6"])
    cost = (
        (input_tokens / 1_000_000) * rates["input"]
        + (output_tokens / 1_000_000) * rates["output"]
        + (cache_creation / 1_000_000) * rates["cache_write"]
        + (cache_read / 1_000_000) * rates["cache_read"]
    )
    return round(cost, 6)


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _current_user_safe() -> str | None:
    """Return logged-in user email or None. Never raises."""
    try:
        from auth.login import get_current_user_or_none
        return get_current_user_or_none()
    except Exception:
        return None


def _user_role_safe(user: str) -> str:
    """Return RBAC role for a user, defaulting to 'viewer' on any failure."""
    try:
        from auth.login import get_role
        return get_role(user) or "viewer"
    except Exception:
        return "viewer"


class ClaudeWrapper:
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model
        self.client = anthropic.Anthropic(api_key=_resolve_api_key())

    def stream_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        stream_placeholder=None,
        progress_label: str = "Generating",
    ) -> tuple[dict, dict]:
        from engine.spend_quota import check_quota, record_spend, QuotaExceededError
        from engine import audit as _audit

        _user = _current_user_safe()
        if _user:
            _role = _user_role_safe(_user)
            allowed, remaining = check_quota(_user, _role)
            if not allowed:
                try:
                    _audit.log_action(
                        "quota_block", _user, 0.0,
                        {"role": _role, "remaining_usd": remaining,
                         "call_kind": progress_label},
                    )
                except Exception:
                    pass
                raise QuotaExceededError(
                    f"Daily Claude spend cap reached for role '{_role}'. "
                    f"Remaining today: ${max(remaining, 0.0):.2f}."
                )

        full_text = ""
        final_usage = None

        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=[{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            for text in stream.text_stream:
                full_text += text
                if stream_placeholder is not None:
                    stream_placeholder.text(f"{progress_label}... {len(full_text)} chars")
            final_message = stream.get_final_message()
            final_usage = final_message.usage

        cleaned = _strip_json_fences(full_text)
        parsed = json.loads(cleaned)

        input_tokens = getattr(final_usage, "input_tokens", 0) or 0
        output_tokens = getattr(final_usage, "output_tokens", 0) or 0
        cache_creation = getattr(final_usage, "cache_creation_input_tokens", 0) or 0
        cache_read = getattr(final_usage, "cache_read_input_tokens", 0) or 0

        cost = _calculate_cost(
            self.model, input_tokens, output_tokens, cache_creation, cache_read
        )

        usage_dict = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_creation_input_tokens": cache_creation,
            "cache_read_input_tokens": cache_read,
            "cost_usd": cost,
            "model": self.model,
        }

        _get_usage_log().append(usage_dict)

        if _user:
            try:
                record_spend(_user, cost, self.model, progress_label)
            except Exception:
                pass
            try:
                _audit.log_action(
                    f"claude_call:{progress_label}",
                    _user,
                    cost,
                    {
                        "model": self.model,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cache_read": cache_read,
                        "cache_creation": cache_creation,
                    },
                )
            except Exception:
                pass

        return parsed, usage_dict


def get_session_usage() -> dict:
    log = _get_usage_log()
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "total_cost_usd": 0.0,
        "call_count": len(log),
    }
    for entry in log:
        totals["input_tokens"] += entry.get("input_tokens", 0)
        totals["output_tokens"] += entry.get("output_tokens", 0)
        totals["cache_creation_input_tokens"] += entry.get("cache_creation_input_tokens", 0)
        totals["cache_read_input_tokens"] += entry.get("cache_read_input_tokens", 0)
        totals["total_cost_usd"] += entry.get("cost_usd", 0.0)
    totals["total_cost_usd"] = round(totals["total_cost_usd"], 6)
    return totals


def reset_session_usage() -> None:
    if _HAS_ST:
        try:
            st.session_state["claude_usage_log"] = []
            return
        except Exception:
            pass
    _FALLBACK_USAGE_LOG.clear()
