"""
Tab 2: Gap Assessment
3 safeguard categories, Required vs Addressable, per-control scoring.
Claude call #1 on "Run Assessment".
"""
import streamlit as st
import plotly.graph_objects as go
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.control_mapper import load_controls, map_connector_findings, merge_assessments
from engine.scorer import compute_readiness, GAP_TIERS, get_readiness_band
from engine.roadmap_generator import score_assessment_with_claude
from data.sample_assessment import DEMO_CONTROL_STATUSES, DEMO_ORG_CONTEXT
from auth.login import require_login, get_current_user_or_none
from storage.github_jsonl import append_record
from storage.evidence import (
    upload_file,
    add_url,
    list_evidence,
    get_evidence_bytes,
    delete_evidence,
)
from engine.audit import log_action
require_login()
current_user = get_current_user_or_none()

st.set_page_config(page_title="Gap Assessment · HIPAA Agent", layout="wide")
st.markdown("# Gap Assessment")
st.caption("HIPAA Security Rule · 42 controls · Administrative · Physical · Technical")

controls = load_controls()
ctrl_map = {c["id"]: c for c in controls}

# ── Status badge helpers ──────────────────────────────────────────────────────
STATUS_COLORS = {
    "Implemented": ("#22C55E", "#052e16"),
    "N/A (Documented)": ("#22C55E", "#052e16"),
    "Partial": ("#EAB308", "#422006"),
    "Not Implemented": ("#6B7280", "#1c1c1c"),
}
SPEC_COLORS = {
    "Required": ("#EF4444", "#7f1d1d"),
    "Addressable": ("#F97316", "#431407"),
}
GAP_LABEL_COLORS = {
    "CRITICAL": "#DC2626",
    "HIGH": "#F97316",
    "MEDIUM": "#EAB308",
    "LOW": "#22C55E",
}


def status_badge(status: str) -> str:
    color, bg = STATUS_COLORS.get(status, ("#9ca3af", "#1c1c1c"))
    return f"<span style='background:{bg};color:{color};padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600'>{status}</span>"


def spec_badge(spec: str) -> str:
    color, bg = SPEC_COLORS.get(spec, ("#9ca3af", "#1c1c1c"))
    return f"<span style='background:{bg};color:{color};padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600'>{spec}</span>"


def gap_badge(tier: str) -> str:
    color = GAP_LABEL_COLORS.get(tier, "#6B7280")
    return f"<span style='color:{color};font-weight:700'>{tier}</span>"


# ── Load or initialize assessment state ───────────────────────────────────────
if "control_statuses" not in st.session_state:
    st.session_state.control_statuses = {}

demo_mode = st.session_state.get("demo_mode", False)

# Pre-populate with demo data if in demo mode and no run yet
if demo_mode and not st.session_state.get("assessment_run"):
    st.session_state.control_statuses = dict(DEMO_CONTROL_STATUSES)
elif not st.session_state.control_statuses:
    # Auto-map from connector findings
    connector_findings = st.session_state.get("connector_findings", {})
    if connector_findings:
        auto = map_connector_findings(connector_findings, controls)
        st.session_state.control_statuses = merge_assessments(auto, st.session_state.get("manual_overrides", {}))

# ── Run Assessment button ─────────────────────────────────────────────────────
col_btn, col_info = st.columns([2, 5])
with col_btn:
    run_clicked = st.button("▶ Run Assessment", type="primary", use_container_width=True)
with col_info:
    st.caption("Scores all 42 controls, calls Claude to identify gaps and risk tiers.")

if run_clicked:
    org_context = {
        "org_name": st.session_state.get("org_name", "Demo Org"),
        "entity_type": st.session_state.get("entity_type", "Business Associate"),
        "ephi_systems": st.session_state.get("ephi_systems", []),
        "ephi_leaves_org": st.session_state.get("ephi_leaves_org", False),
        "soc2_status": st.session_state.get("soc2_status", "None"),
        "remote_workforce": st.session_state.get("remote_workforce", False),
        "workforce_size": st.session_state.get("workforce_size", 50),
    }
    if demo_mode:
        org_context.update(DEMO_ORG_CONTEXT)

    statuses = st.session_state.control_statuses
    if not statuses:
        st.warning("No control data available. Connect integrations or enable Demo Mode.")
    else:
        readiness = compute_readiness(controls, statuses)
        st.session_state.readiness_results = readiness
        st.session_state.assessment_run = True

        # Claude call #1
        api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
        if api_key:
            with st.spinner("Claude is analyzing your control gaps..."):
                placeholder = st.empty()
                try:
                    claude_result = score_assessment_with_claude(
                        statuses, controls,
                        st.session_state.get("connector_findings", {}),
                        org_context, placeholder
                    )
                    st.session_state.claude_analysis = claude_result
                    placeholder.empty()
                except Exception as e:
                    placeholder.empty()
                    st.warning(f"Claude analysis unavailable: {e}")
        else:
            st.info("Add ANTHROPIC_API_KEY to secrets for AI-powered gap analysis.")

        st.rerun()

# ── Render results if assessment run ─────────────────────────────────────────
if st.session_state.get("assessment_run") and st.session_state.get("readiness_results"):
    r = st.session_state.readiness_results
    org_name = st.session_state.get("org_name", "Organization")

    # ── Gauge chart ───────────────────────────────────────────────────────────
    score = r["overall"]
    band = r["band_label"]
    band_color = r["band_color"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number={"suffix": "%", "font": {"size": 36, "color": band_color}},
        title={"text": f"Overall HIPAA Readiness · {band}", "font": {"size": 16, "color": "#E2E8F0"}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"color": "#E2E8F0"}},
            "bar": {"color": band_color, "thickness": 0.25},
            "bgcolor": "#12121A",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "#450a0a"},
                {"range": [50, 75], "color": "#422006"},
                {"range": [75, 90], "color": "#431407"},
                {"range": [90, 100], "color": "#052e16"},
            ],
            "threshold": {"line": {"color": band_color, "width": 4}, "thickness": 0.75, "value": score},
        },
    ))
    fig.update_layout(
        paper_bgcolor="#0A0A0F", font_color="#E2E8F0",
        height=280, margin=dict(t=40, b=20, l=30, r=30)
    )

    col_gauge, col_cats = st.columns([2, 3])
    with col_gauge:
        st.plotly_chart(fig, use_container_width=True)

    with col_cats:
        st.markdown("#### Readiness by Category")
        cat_scores = r.get("category_scores", {})
        for cat, cat_score in cat_scores.items():
            cat_band, cat_color = get_readiness_band(cat_score)
            col_label, col_bar = st.columns([1, 3])
            col_label.markdown(f"**{cat}**")
            col_bar.progress(int(cat_score), text=f"{cat_score:.1f}% · {cat_band}")

        st.markdown("#### Control Summary")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Total Controls", r["total_controls"])
        mc2.metric("Implemented", r["implemented_count"], delta_color="normal")
        mc3.metric("Partial", r["partial_count"], delta_color="off")
        mc4.metric("Not Implemented", r["not_implemented_count"], delta_color="inverse")

    # ── Claude gap callouts ───────────────────────────────────────────────────
    claude = st.session_state.get("claude_analysis")
    if claude:
        st.divider()
        risk_tier = claude.get("overall_risk_tier", "UNKNOWN")
        risk_color = GAP_LABEL_COLORS.get(risk_tier, "#6B7280")
        st.markdown(
            f"<div style='background:#12121A;border-left:4px solid {risk_color};"
            f"padding:12px 16px;border-radius:4px;margin-bottom:8px'>"
            f"<strong style='color:{risk_color}'>Risk Tier: {risk_tier}</strong> · "
            f"{claude.get('gap_summary', '')}</div>",
            unsafe_allow_html=True
        )
        if claude.get("audit_exposure"):
            st.markdown(
                f"<div style='background:#12121A;border-left:4px solid #6366F1;"
                f"padding:12px 16px;border-radius:4px;margin-bottom:8px'>"
                f"<strong style='color:#818CF8'>Auditor Would Flag First:</strong> "
                f"{claude['audit_exposure']}</div>",
                unsafe_allow_html=True
            )

        cols = st.columns(2)
        with cols[0]:
            if claude.get("critical_gaps"):
                st.markdown("#### Critical Gaps")
                for g in claude["critical_gaps"]:
                    c = ctrl_map.get(g["control_id"], {})
                    st.markdown(
                        f"<div style='background:#450a0a;border:1px solid #DC2626;"
                        f"padding:10px;border-radius:6px;margin-bottom:6px'>"
                        f"<strong style='color:#DC2626'>{g['control_id']}</strong> · "
                        f"{c.get('spec', '')} [{c.get('standard', '')}]<br>"
                        f"<span style='color:#fca5a5;font-size:12px'>{g.get('reason', '')}</span><br>"
                        f"<em style='color:#f87171;font-size:11px'>Action: {g.get('immediate_action', '')}</em>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
        with cols[1]:
            if claude.get("quick_wins"):
                st.markdown("#### Quick Wins")
                for w in claude["quick_wins"]:
                    c = ctrl_map.get(w["control_id"], {})
                    st.markdown(
                        f"<div style='background:#052e16;border:1px solid #22C55E;"
                        f"padding:10px;border-radius:6px;margin-bottom:6px'>"
                        f"<strong style='color:#22C55E'>{w['control_id']}</strong> · "
                        f"{c.get('spec', '')}<br>"
                        f"<span style='color:#86efac;font-size:12px'>{w.get('action', '')}</span><br>"
                        f"<em style='color:#6ee7b7;font-size:11px'>Effort: ~{w.get('effort_days', '?')} day(s)</em>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

    st.divider()

    # ── Control cards per safeguard ───────────────────────────────────────────
    safeguards = ["Administrative", "Physical", "Technical"]
    control_results = r.get("control_results", {})
    statuses = st.session_state.control_statuses

    for safeguard in safeguards:
        cat_controls = [c for c in controls if c["safeguard"] == safeguard]
        cat_score = r.get("category_scores", {}).get(safeguard, 0)
        cat_band, cat_color = get_readiness_band(cat_score)

        required_count = len([c for c in cat_controls if c["status"] == "Required"])
        addressable_count = len([c for c in cat_controls if c["status"] == "Addressable"])

        with st.expander(
            f"**{safeguard} Safeguards** · {cat_score:.1f}% {cat_band} "
            f"({required_count} Required · {addressable_count} Addressable)",
            expanded=(safeguard == "Administrative"),
        ):
            # Filter controls by gap tier for quick navigation
            filter_col, _ = st.columns([2, 5])
            tier_filter = filter_col.selectbox(
                "Filter by gap tier",
                ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
                key=f"filter_{safeguard}",
            )

            for ctrl in cat_controls:
                ctrl_id = ctrl["id"]
                result = control_results.get(ctrl_id, {})
                gap_tier = result.get("gap_tier", "LOW")

                if tier_filter != "All" and gap_tier != tier_filter:
                    continue

                gap_color = GAP_LABEL_COLORS.get(gap_tier, "#6B7280")
                ctrl_score = result.get("score", 0)
                current_status = result.get("status", "Not Implemented")
                raw_evidence = result.get("evidence", False)
                user_evidence_items = list_evidence(current_user, control_id=ctrl_id) if current_user else []
                evidence = bool(user_evidence_items) if current_user and user_evidence_items else raw_evidence
                notes = result.get("notes", "")

                with st.container():
                    st.markdown(
                        f"<div style='background:#12121A;border:1px solid #1e1e2e;"
                        f"border-left:4px solid {gap_color};"
                        f"padding:12px 16px;border-radius:6px;margin-bottom:8px'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center'>"
                        f"<div>"
                        f"<strong style='color:#E2E8F0'>{ctrl_id}</strong> "
                        f"{spec_badge(ctrl['status'])} "
                        f"&nbsp;<span style='color:#94a3b8;font-size:13px'>{ctrl['standard']} / {ctrl['spec']}</span>"
                        f"</div>"
                        f"<div style='text-align:right'>"
                        f"<span style='color:{gap_color};font-size:12px;font-weight:700'>{gap_tier}</span> "
                        f"<span style='color:#94a3b8;font-size:12px'>· {ctrl_score} pts</span>"
                        f"</div>"
                        f"</div>"
                        f"<div style='margin-top:6px'>"
                        f"{status_badge(current_status)} "
                        f"<span style='color:#94a3b8;font-size:12px'>Evidence: {'✅' if evidence else '❌'}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    citation = ctrl.get("cfr_citation", "")
                    if citation:
                        st.caption(citation)

                    if notes:
                        st.markdown(
                            f"<div style='background:#12121A;color:#94a3b8;font-size:12px;"
                            f"font-style:italic;padding:4px 0'>{notes}</div>",
                            unsafe_allow_html=True
                        )

                    with st.expander("Evidence", expanded=False):
                        if current_user is None:
                            st.info("Log in to attach evidence.")
                        else:
                            items = list_evidence(current_user, control_id=ctrl_id)
                            if items:
                                for ev in items:
                                    cols = st.columns([4, 2, 1])
                                    cols[0].markdown(
                                        f"**{ev['filename']}**  ·  {ev.get('caption', '')}"
                                    )
                                    cols[1].caption(ev.get("_ts", ""))
                                    if cols[2].button("Delete", key=f"del_{ev['evidence_id']}"):
                                        delete_evidence(current_user, ev["evidence_id"])
                                        st.rerun()
                                    if ev.get("kind") == "url":
                                        st.link_button("Open URL", ev.get("url", ""))
                                    else:
                                        evidence_bytes_tuple = get_evidence_bytes(
                                            current_user, ev["evidence_id"]
                                        )
                                        if evidence_bytes_tuple:
                                            bytes_, fname, ctype = evidence_bytes_tuple
                                            st.download_button(
                                                "Download",
                                                bytes_,
                                                file_name=fname,
                                                mime=ctype or "application/octet-stream",
                                                key=f"dl_{ev['evidence_id']}",
                                            )
                            else:
                                st.caption("No evidence attached yet.")

                            upload_kind = st.radio(
                                "Add evidence as",
                                ["File upload", "URL reference"],
                                key=f"kind_{ctrl_id}",
                                horizontal=True,
                            )
                            caption_val = st.text_input(
                                "Caption (optional)", key=f"cap_{ctrl_id}"
                            )
                            if upload_kind == "File upload":
                                f = st.file_uploader(
                                    "PDF, PNG, JPG, CSV, TXT (max 10 MB)",
                                    type=["pdf", "png", "jpg", "jpeg", "csv", "txt"],
                                    key=f"up_{ctrl_id}",
                                )
                                if f and st.button("Save file", key=f"save_ev_{ctrl_id}"):
                                    try:
                                        upload_file(
                                            current_user,
                                            ctrl_id,
                                            f.name,
                                            f.read(),
                                            caption_val,
                                            f.type,
                                        )
                                        st.success("Saved.")
                                        st.rerun()
                                    except ValueError as e:
                                        st.error(str(e))
                            else:
                                url_val = st.text_input("URL", key=f"url_{ctrl_id}")
                                if url_val and st.button("Save URL", key=f"save_url_{ctrl_id}"):
                                    try:
                                        add_url(current_user, ctrl_id, url_val, caption_val)
                                        st.success("Saved.")
                                        st.rerun()
                                    except ValueError as e:
                                        st.error(str(e))

                    with st.expander(f"Override · {ctrl_id}", expanded=False):
                        col_s, col_e, col_a = st.columns(3)
                        status_options = ["Implemented", "Partial", "Not Implemented", "N/A (Documented)"]
                        new_status = col_s.selectbox(
                            "Status",
                            status_options,
                            index=status_options.index(current_status) if current_status in status_options else 2,
                            key=f"status_{ctrl_id}",
                        )
                        new_evidence = col_e.toggle("Evidence Present", value=evidence, key=f"ev_{ctrl_id}")
                        new_alt = None
                        if ctrl["status"] == "Addressable":
                            new_alt = col_a.toggle(
                                "Alt. control documented?",
                                value=result.get("alt_documented") or False,
                                key=f"alt_{ctrl_id}",
                            )
                        new_notes = st.text_input(
                            "Notes",
                            value=notes,
                            key=f"notes_{ctrl_id}",
                            placeholder="Add context...",
                        )
                        if st.button("Save Override", key=f"save_{ctrl_id}"):
                            st.session_state.control_statuses[ctrl_id] = {
                                "status": new_status,
                                "evidence": new_evidence,
                                "alt_documented": new_alt,
                                "notes": new_notes,
                            }
                            st.success("Saved. Click 'Run Assessment' to recalculate.")

                    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### Save to history")
    save_user = get_current_user_or_none()
    save_disabled = not bool(save_user)
    if st.button("Save assessment to history", disabled=save_disabled):
        org_for_save = st.session_state.get("org_name", "Organization")
        try:
            append_record(save_user, "assessments", {
                "org_name": org_for_save,
                "overall_score": float(r.get("overall", 0.0) or 0.0),
                "band_label": r.get("band_label", ""),
                "critical_gaps": r.get("critical_gaps", []) or [],
                "high_gaps": r.get("high_gaps", []) or [],
                "full_results": r,
            })
            try:
                log_action("assessment_save", save_user, 0.0, {
                    "org_name": org_for_save,
                    "overall_score": float(r.get("overall", 0.0) or 0.0),
                })
            except Exception as audit_err:
                st.caption(f"Audit log skipped: {audit_err}")
            st.success("Saved to history. Open the History page to review.")
        except Exception as save_err:
            st.warning(f"Save to history failed: {save_err}")

    st.divider()
    st.markdown("### Export Assessment")
    from utils.csv_exporter import export_assessment_csv
    from utils.pdf_exporter import generate_assessment_pdf
    from engine.baa_engine import baa_summary as compute_baa_summary

    baa_list = st.session_state.get("baa_list") or []
    baa_sum = compute_baa_summary(baa_list) if baa_list else {"total": 0, "ephi_vendors": 0, "missing_baas": 0, "expired": 0, "expiring_90d": 0, "compliance_rate": 0}

    org_ctx = {
        "org_name": st.session_state.get("org_name", "Organization"),
        "entity_type": st.session_state.get("entity_type", ""),
        "ephi_systems": st.session_state.get("ephi_systems", []),
        "soc2_status": st.session_state.get("soc2_status", "None"),
    }

    col_csv, col_pdf = st.columns(2)
    with col_csv:
        csv_data = export_assessment_csv(r, controls, org_ctx["org_name"])
        st.download_button(
            "Download CSV Assessment",
            data=csv_data,
            file_name=f"hipaa_assessment_{org_ctx['org_name'].lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )
    with col_pdf:
        try:
            pdf_data = generate_assessment_pdf(org_ctx, r, controls, baa_sum, st.session_state.get("claude_analysis"))
            st.download_button(
                "Download PDF Report",
                data=pdf_data,
                file_name=f"hipaa_report_{org_ctx['org_name'].lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.warning(f"PDF export unavailable: {e}")

else:
    # No assessment run yet
    st.info("Click **Run Assessment** to score all 42 HIPAA Security Rule controls.", icon="▶")

    # Show all controls in read-only mode
    st.markdown("### Control Library Preview")
    for safeguard in ["Administrative", "Physical", "Technical"]:
        cat_controls = [c for c in controls if c["safeguard"] == safeguard]
        req = len([c for c in cat_controls if c["status"] == "Required"])
        addr = len([c for c in cat_controls if c["status"] == "Addressable"])
        with st.expander(f"**{safeguard}** · {len(cat_controls)} controls ({req} Required · {addr} Addressable)"):
            for ctrl in cat_controls:
                st.markdown(
                    f"**{ctrl['id']}** {spec_badge(ctrl['status'])} "
                    f"· {ctrl['standard']} / **{ctrl['spec']}**",
                    unsafe_allow_html=True
                )
                preview_citation = ctrl.get("cfr_citation", "")
                if preview_citation:
                    st.caption(preview_citation)
                st.caption(ctrl["description"])
