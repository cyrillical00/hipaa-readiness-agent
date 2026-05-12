"""Tab 6 Assessment History, roadmap state, audit log, and daily spend."""
import streamlit as st
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth.login import require_login, get_role
from storage.github_jsonl import list_records, get_storage_mode
from engine.audit import get_audit_records, export_audit_csv
from engine.spend_quota import get_today_spend, ROLE_DAILY_QUOTA_USD

st.set_page_config(page_title="History HIPAA Agent", layout="wide")
st.markdown("# Assessment History")

current_user = require_login()
current_role = get_role(current_user)

st.markdown(
    f"<div style='background:#12121A;border:1px solid #1e1e2e;"
    f"border-left:4px solid #6366F1;padding:8px 14px;border-radius:6px;"
    f"margin-bottom:8px'>"
    f"<span style='color:#94a3b8;font-size:12px'>Logged in as</span> "
    f"<strong style='color:#E2E8F0'>{current_user}</strong> "
    f"<span style='color:#818CF8;font-size:12px'>· role: {current_role}</span>"
    f"</div>",
    unsafe_allow_html=True,
)

mode = get_storage_mode()
if mode == "github":
    repo = os.environ.get("HIPAA_STATE_REPO", "")
    try:
        repo = st.secrets.get("HIPAA_STATE_REPO", repo)
    except Exception:
        pass
    storage_label = f"GitHub: {repo or 'cyrillical00/hipaa-state'}"
else:
    storage_label = "Local disk"
st.caption(f"Storage mode: {storage_label}")

st.divider()

assessments = list_records(current_user, "assessments")
assessments.sort(key=lambda r: r.get("_ts", ""), reverse=True)

st.markdown("## Past assessments")

if not assessments:
    st.info("No saved assessments yet. Run a Gap Assessment and click 'Save to history'.")
else:
    rows = []
    for idx, rec in enumerate(assessments):
        rows.append({
            "Row": idx,
            "Timestamp": rec.get("_ts", ""),
            "Org": rec.get("org_name", ""),
            "Score": round(float(rec.get("overall_score", 0.0) or 0.0), 1),
            "Band": rec.get("band_label", ""),
            "Critical": len(rec.get("critical_gaps", []) or []),
            "High": len(rec.get("high_gaps", []) or []),
        })
    a_df = pd.DataFrame(rows)
    selection = st.dataframe(
        a_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        key="assessments_table",
    )

    selected_rows = []
    try:
        selected_rows = selection.selection.rows  # type: ignore[attr-defined]
    except Exception:
        selected_rows = []

    btn_col1, btn_col2 = st.columns([1, 1])

    with btn_col1:
        load_disabled = len(selected_rows) != 1
        if st.button("Load into session", disabled=load_disabled, use_container_width=True):
            rec = assessments[selected_rows[0]]
            full = rec.get("full_results") or {}
            if full:
                st.session_state["readiness_results"] = full
                st.session_state["assessment_run"] = True
            org = rec.get("org_name") or ""
            if org:
                st.session_state["org_name"] = org
            st.success("Loaded into session. Open the Gap Assessment page to view.")

    with btn_col2:
        diff_disabled = len(selected_rows) != 2
        diff_clicked = st.button(
            "Diff selected", disabled=diff_disabled, use_container_width=True
        )

    if not diff_disabled and diff_clicked:
        a = assessments[selected_rows[0]]
        b = assessments[selected_rows[1]]
        a_score = float(a.get("overall_score", 0.0) or 0.0)
        b_score = float(b.get("overall_score", 0.0) or 0.0)

        def _ids(records):
            out = set()
            for g in records or []:
                if isinstance(g, dict) and g.get("control_id"):
                    out.add(g["control_id"])
                elif isinstance(g, str):
                    out.add(g)
            return out

        a_crit = _ids(a.get("critical_gaps"))
        b_crit = _ids(b.get("critical_gaps"))
        a_high = _ids(a.get("high_gaps"))
        b_high = _ids(b.get("high_gaps"))

        st.markdown("### Diff")
        d1, d2 = st.columns(2)
        with d1:
            st.markdown(f"**A · {a.get('_ts', '')}**")
            st.metric("Score", f"{a_score:.1f}%")
            st.metric("Critical gaps", len(a_crit))
            st.metric("High gaps", len(a_high))
            st.caption(f"Org: {a.get('org_name', '')}")
        with d2:
            st.markdown(f"**B · {b.get('_ts', '')}**")
            st.metric("Score", f"{b_score:.1f}%", delta=f"{b_score - a_score:+.1f}")
            st.metric("Critical gaps", len(b_crit), delta=len(b_crit) - len(a_crit))
            st.metric("High gaps", len(b_high), delta=len(b_high) - len(a_high))
            st.caption(f"Org: {b.get('org_name', '')}")

        st.markdown("#### Critical gap changes")
        added_c = sorted(b_crit - a_crit)
        removed_c = sorted(a_crit - b_crit)
        c1, c2 = st.columns(2)
        c1.markdown("**Added in B**")
        c1.write(added_c or "None")
        c2.markdown("**Resolved (only in A)**")
        c2.write(removed_c or "None")

        st.markdown("#### High gap changes")
        added_h = sorted(b_high - a_high)
        removed_h = sorted(a_high - b_high)
        h1, h2 = st.columns(2)
        h1.markdown("**Added in B**")
        h1.write(added_h or "None")
        h2.markdown("**Resolved (only in A)**")
        h2.write(removed_h or "None")

st.divider()

st.markdown("## Roadmap state")
roadmap_state = list_records(current_user, "roadmap_state")
roadmap_state.sort(key=lambda r: r.get("_ts", ""), reverse=True)

if not roadmap_state:
    st.info("No roadmap snapshots yet. Generate a roadmap on the Remediation Roadmap page.")
else:
    rs_rows = []
    for rec in roadmap_state:
        total = int(rec.get("items_total", 0) or 0)
        done = int(rec.get("items_complete", 0) or 0)
        pct = round((done / total) * 100, 1) if total > 0 else 0.0
        rs_rows.append({
            "Timestamp": rec.get("_ts", ""),
            "Roadmap ID": rec.get("roadmap_id", "")[:8],
            "Items total": total,
            "Items complete": done,
            "Progress %": pct,
        })
    st.dataframe(pd.DataFrame(rs_rows), use_container_width=True, hide_index=True)

st.divider()

st.markdown("## Audit log (last 50)")
audit = get_audit_records(current_user, limit=50)
if not audit:
    st.info("No audit events yet.")
else:
    audit_rows = []
    for rec in audit:
        meta = rec.get("metadata") or {}
        if isinstance(meta, dict):
            meta_summary = ", ".join(f"{k}={v}" for k, v in meta.items())
        else:
            meta_summary = str(meta)
        audit_rows.append({
            "Timestamp": rec.get("_ts", ""),
            "Action": rec.get("action", ""),
            "Cost USD": round(float(rec.get("cost_usd", 0.0) or 0.0), 6),
            "Metadata": meta_summary,
        })
    st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
    st.download_button(
        "Download audit CSV",
        data=export_audit_csv(current_user),
        file_name=f"hipaa_audit_{current_user.replace('@', '_at_')}.csv",
        mime="text/csv",
    )

st.divider()

st.markdown("## Today's spend")
spent = get_today_spend(current_user)
quota = ROLE_DAILY_QUOTA_USD.get(current_role, 0.0)
if quota == float("inf"):
    quota_label = "Unlimited"
    remaining_label = "Unlimited"
else:
    quota_label = f"${quota:.2f}"
    remaining = max(quota - spent, 0.0)
    remaining_label = f"${remaining:.2f}"

s1, s2, s3 = st.columns(3)
s1.metric("Spent today (USD)", f"${spent:.4f}")
s2.metric(f"Quota ({current_role})", quota_label)
s3.metric("Remaining", remaining_label)
