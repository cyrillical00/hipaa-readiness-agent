"""
Tab 5 — Remediation Roadmap
Claude-generated phased action plan, exportable as CSV.
"""
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.roadmap_generator import generate_roadmap
from engine.soc2_crosswalk import load_crosswalk, compute_overlap
from engine.baa_engine import baa_summary as compute_baa_summary, enrich_baa_list
from engine.control_mapper import load_controls
from engine.validator import validate_roadmap
from engine.spend_quota import QuotaExceededError
from data.sample_assessment import DEMO_ORG_CONTEXT
from data.sample_baas import DEMO_BAAS
from utils.csv_exporter import export_roadmap_csv
from ui.cost_panel import render_cost_panel
from auth.login import require_login, get_current_user_or_none
from storage.github_jsonl import append_record
from uuid import uuid4
require_login()

st.set_page_config(page_title="Remediation Roadmap — HIPAA Agent", layout="wide")
st.markdown("# Remediation Roadmap")
st.caption(
    "Claude analyzes your gap assessment, BAA risks, and SOC2 overlap to generate "
    "a phased, prioritized action plan."
)

render_cost_panel()

controls = load_controls()
crosswalk = load_crosswalk()
soc2_status = st.session_state.get("soc2_status", "None")
demo_mode = st.session_state.get("demo_mode", False)

# ── Prerequisites check ───────────────────────────────────────────────────────
readiness = st.session_state.get("readiness_results")
baa_list = st.session_state.get("baa_list")

if not readiness:
    if demo_mode:
        # Auto-run assessment for demo
        from engine.control_mapper import map_connector_findings, merge_assessments
        from engine.scorer import compute_readiness
        from connectors.okta import OKTA_DEMO_FINDINGS
        from connectors.aws import AWS_DEMO_FINDINGS
        from connectors.google_workspace import GOOGLE_WORKSPACE_DEMO_FINDINGS
        from connectors.jamf import JAMF_DEMO_FINDINGS
        from data.sample_assessment import DEMO_CONTROL_STATUSES

        demo_findings = {
            "okta": OKTA_DEMO_FINDINGS,
            "aws": AWS_DEMO_FINDINGS,
            "google_workspace": GOOGLE_WORKSPACE_DEMO_FINDINGS,
            "jamf": JAMF_DEMO_FINDINGS,
        }
        auto = map_connector_findings(demo_findings, controls)
        merged = merge_assessments(auto, DEMO_CONTROL_STATUSES)
        readiness = compute_readiness(controls, merged)
        st.session_state.readiness_results = readiness
        st.session_state.control_statuses = merged
        st.session_state.assessment_run = True
    else:
        st.warning("Run the **Gap Assessment** first to generate a roadmap.")
        st.stop()

if not baa_list and demo_mode:
    baa_list = enrich_baa_list(DEMO_BAAS)
    st.session_state.baa_list = baa_list

baa_sum = compute_baa_summary(baa_list) if baa_list else {
    "total": 0, "ephi_vendors": 0, "missing_baas": 0,
    "expired": 0, "expiring_90d": 0, "compliance_rate": 100,
    "critical": 0, "high": 0,
}
overlap = compute_overlap(crosswalk, soc2_status)

org_context = {
    "org_name": st.session_state.get("org_name", "Demo Org"),
    "entity_type": st.session_state.get("entity_type", "Business Associate"),
    "ephi_systems": st.session_state.get("ephi_systems", []),
    "ephi_leaves_org": st.session_state.get("ephi_leaves_org", False),
    "soc2_status": soc2_status,
    "remote_workforce": st.session_state.get("remote_workforce", False),
    "workforce_size": st.session_state.get("workforce_size", 50),
}
if demo_mode:
    org_context.update(DEMO_ORG_CONTEXT)

# ── Input summary ─────────────────────────────────────────────────────────────
score = readiness.get("overall", 0)
band = readiness.get("band_label", "")
band_color = readiness.get("band_color", "#6B7280")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Readiness Score", f"{score:.1f}%", delta=band)
col2.metric("Critical Gaps", len(readiness.get("critical_gaps", [])), delta_color="inverse")
col3.metric("Critical BAA Gaps", baa_sum.get("critical", 0), delta_color="inverse")
col4.metric("SOC2 Coverage", f"{overlap['coverage_pct']:.0f}%")

# ── Generate button ───────────────────────────────────────────────────────────
st.divider()
col_btn, col_desc = st.columns([2, 5])
with col_btn:
    gen_clicked = st.button("✨ Generate Roadmap", type="primary", use_container_width=True)
with col_desc:
    st.caption(
        "Claude writes a 3-phase remediation plan: Phase 1 (0–30d Critical), "
        "Phase 2 (31–90d Policy), Phase 3 (91–180d Audit Prep)."
    )

if gen_clicked:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
    if not api_key:
        st.error("ANTHROPIC_API_KEY not configured. Add it to .streamlit/secrets.toml.")
    else:
        with st.spinner("Claude is generating your HIPAA remediation roadmap..."):
            progress_placeholder = st.empty()
            try:
                roadmap = generate_roadmap(
                    readiness, controls, baa_sum, overlap, org_context, progress_placeholder
                )
                st.session_state.roadmap = roadmap
                critical_gaps = readiness.get("critical_gaps", [])
                high_gaps = readiness.get("high_gaps", [])
                st.session_state.roadmap_validation = validate_roadmap(
                    roadmap, critical_gaps, high_gaps, controls
                )
                save_user = get_current_user_or_none()
                if save_user:
                    try:
                        items_total = sum(
                            len(p.get("items", []) or []) for p in roadmap.get("phases", []) or []
                        )
                        append_record(save_user, "roadmap_state", {
                            "roadmap_id": str(uuid4()),
                            "items_total": items_total,
                            "items_complete": 0,
                        })
                    except Exception as snap_err:
                        st.caption(f"Roadmap snapshot skipped: {snap_err}")
                progress_placeholder.empty()
                st.rerun()
            except QuotaExceededError as qe:
                progress_placeholder.empty()
                st.error(f"Daily spend quota exceeded: {qe}")
            except Exception as e:
                progress_placeholder.empty()
                st.error(f"Roadmap generation failed: {e}")

# ── Render roadmap ────────────────────────────────────────────────────────────
roadmap = st.session_state.get("roadmap")
if roadmap:
    validation = st.session_state.get("roadmap_validation")
    if validation:
        v_status = validation.get("status", "")
        v_notes = validation.get("notes", "") or ""
        v_missing = validation.get("missing_controls", []) or []
        v_hallucinated = validation.get("hallucinated_controls", []) or []
        if v_status == "pass":
            msg = "Validator: roadmap addresses all critical gaps."
            if v_notes:
                msg = f"{msg} {v_notes}"
            st.success(msg)
        elif v_status == "warn":
            st.warning(f"Validator flagged issues. Missing critical controls: {v_missing}. {v_notes}")
        elif v_status == "fail":
            st.error(f"Validator FAILED. Hallucinated controls: {v_hallucinated}. {v_notes}")

    # Executive summary
    risk_tier = roadmap.get("overall_risk_tier", "UNKNOWN")
    risk_colors = {"CRITICAL": "#DC2626", "HIGH": "#F97316", "MEDIUM": "#EAB308", "LOW": "#22C55E"}
    risk_color = risk_colors.get(risk_tier, "#6B7280")

    st.markdown(
        f"<div style='background:#12121A;border-left:4px solid {risk_color};"
        f"padding:14px 18px;border-radius:6px;margin-bottom:12px'>"
        f"<strong style='color:{risk_color}'>Risk Tier: {risk_tier}</strong><br>"
        f"<span style='color:#E2E8F0'>{roadmap.get('executive_summary', '')}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Quick wins
    if roadmap.get("quick_wins"):
        with st.expander("⚡ Quick Wins (Low Effort, High Impact)", expanded=True):
            cols = st.columns(min(len(roadmap["quick_wins"]), 3))
            for i, win in enumerate(roadmap["quick_wins"]):
                with cols[i % 3]:
                    st.markdown(
                        f"<div style='background:#052e16;border:1px solid #22C55E;"
                        f"padding:12px;border-radius:6px;height:100%'>"
                        f"<strong style='color:#22C55E'>{win.get('control_id', '')}</strong><br>"
                        f"<span style='color:#E2E8F0;font-size:13px'>{win.get('title', '')}</span><br>"
                        f"<span style='color:#86efac;font-size:12px'>{win.get('description', '')}</span><br>"
                        f"<em style='color:#6ee7b7;font-size:11px'>Effort: {win.get('effort', '?')} · Impact: {win.get('impact', '?')}</em>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

    st.divider()

    # Phase cards
    phase_colors = {1: "#DC2626", 2: "#F97316", 3: "#6366F1"}
    phase_icons = {1: "🚨", 2: "📋", 3: "🏆"}

    for phase in roadmap.get("phases", []):
        phase_num = phase.get("phase", 1)
        phase_color = phase_colors.get(phase_num, "#6366F1")
        phase_icon = phase_icons.get(phase_num, "📌")
        items = phase.get("items", [])

        priority_counts = {}
        for item in items:
            p = item.get("priority", "MEDIUM")
            priority_counts[p] = priority_counts.get(p, 0) + 1

        counts_str = " · ".join(f"{v} {k}" for k, v in sorted(priority_counts.items()))

        with st.expander(
            f"{phase_icon} **{phase.get('label', f'Phase {phase_num}')}** — {len(items)} actions · {counts_str}",
            expanded=(phase_num == 1),
        ):
            st.caption(phase.get("description", ""))

            # Summary table
            if items:
                import pandas as pd
                df = pd.DataFrame([{
                    "ID": item.get("control_id", ""),
                    "Action": item.get("title", ""),
                    "Owner": item.get("owner_role", ""),
                    "Effort": item.get("effort", ""),
                    "Priority": item.get("priority", ""),
                    "SOC2 Reuse": "✅" if item.get("soc2_reuse") else "—",
                    "Artifact": item.get("expected_artifact", ""),
                } for item in items])
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Priority": st.column_config.TextColumn(width="small"),
                        "Effort": st.column_config.TextColumn(width="small"),
                        "SOC2 Reuse": st.column_config.TextColumn(width="small"),
                    }
                )

            # Detailed cards
            st.markdown("#### Action Details")
            for item in items:
                p = item.get("priority", "MEDIUM")
                item_color = risk_colors.get(p, "#6B7280")
                soc2_note = ""
                if item.get("soc2_reuse") and item.get("soc2_note"):
                    soc2_note = (
                        f"<br><span style='color:#818CF8;font-size:12px'>"
                        f"♻️ SOC2 Reuse: {item['soc2_note']}</span>"
                    )
                st.markdown(
                    f"<div style='background:#12121A;border:1px solid #1e1e2e;"
                    f"border-left:4px solid {item_color};"
                    f"padding:10px 14px;border-radius:6px;margin-bottom:6px'>"
                    f"<div style='display:flex;justify-content:space-between'>"
                    f"<strong style='color:#E2E8F0'>{item.get('control_id', '')}</strong> "
                    f"<span style='color:{item_color};font-size:12px'>{p}</span>"
                    f"</div>"
                    f"<div style='color:#E2E8F0;font-size:13px;margin-top:2px'>"
                    f"{item.get('title', '')}</div>"
                    f"<div style='color:#94a3b8;font-size:12px;margin-top:4px'>"
                    f"{item.get('description', '')}</div>"
                    f"<div style='margin-top:6px'>"
                    f"<span style='color:#64748b;font-size:12px'>"
                    f"Owner: {item.get('owner_role', '')} · "
                    f"Effort: {item.get('effort', '')} · "
                    f"Artifact: {item.get('expected_artifact', '')}"
                    f"</span>"
                    f"{soc2_note}"
                    f"</div></div>",
                    unsafe_allow_html=True
                )

    # ── Export ────────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Export Roadmap")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        csv_data = export_roadmap_csv(roadmap)
        org_name = org_context.get("org_name", "org").lower().replace(" ", "_")
        st.download_button(
            "Download Roadmap CSV (Jira-importable)",
            data=csv_data,
            file_name=f"hipaa_roadmap_{org_name}.csv",
            mime="text/csv",
        )
    with col_e2:
        st.caption(
            "CSV includes Summary, Description, Priority, Estimate, Labels, and Phase — "
            "ready to import directly into Jira as a project sprint."
        )

else:
    if not gen_clicked:
        st.markdown("""
### What the roadmap will include:

**Phase 1 (0–30 days) — Critical Remediation**
- Required controls at 0% (immediate OCR audit risk)
- CRITICAL BAA gaps — vendors with ePHI and no agreement
- Quick wins achievable in < 1 week

**Phase 2 (31–90 days) — Policy & Documentation**
- Addressable controls and policy documentation
- Annual training program
- BAA renewals and sub-contractor disclosures

**Phase 3 (91–180 days) — Audit Readiness**
- DR plan testing and tabletop exercises
- Evidence package preparation
- Third-party assessment preparation

> Click **Generate Roadmap** above to produce your personalized plan.
""")
