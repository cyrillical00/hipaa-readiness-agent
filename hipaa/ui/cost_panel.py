"""Sidebar/inline panel showing per-call Claude usage and session totals."""
import streamlit as st


def _cache_read_pct(totals):
    inp = totals.get("input_tokens", 0)
    cr = totals.get("cache_read_input_tokens", 0)
    cc = totals.get("cache_creation_input_tokens", 0)
    denom = inp + cr + cc
    if denom <= 0:
        return 0.0
    return cr / denom * 100


def render_cost_panel():
    """Render an expander in the current container showing session Claude usage."""
    log = st.session_state.get("claude_usage_log") or []
    with st.expander("Claude usage", expanded=False):
        if not log:
            st.caption("No Claude calls yet this session.")
            return

        try:
            from engine.claude_client import get_session_usage, reset_session_usage
        except Exception as e:
            st.caption(f"Usage tracking unavailable: {e}")
            return

        totals = get_session_usage() or {}
        last_cost = log[-1].get("cost_usd", 0.0) if log else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total cost (USD)", f"${totals.get('total_cost_usd', 0.0):.4f}")
        c2.metric("Calls made", totals.get("call_count", 0))
        c3.metric("Cache reads", f"{_cache_read_pct(totals):.1f}%")
        c4.metric("Last call cost", f"${last_cost:.4f}")

        rows = [
            {
                "time": entry.get("timestamp", ""),
                "model": entry.get("model", ""),
                "input": entry.get("input_tokens", 0),
                "output": entry.get("output_tokens", 0),
                "cache_read": entry.get("cache_read_input_tokens", 0),
                "cost_usd": entry.get("cost_usd", 0.0),
            }
            for entry in reversed(log)
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

        if st.button("Reset session totals", key="cost_panel_reset"):
            reset_session_usage()
            st.session_state["claude_usage_log"] = []
            st.rerun()
