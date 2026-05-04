"""
HIPAA Readiness Agent — Entry Point
Org context selector + session state initialization.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from ui.cost_panel import render_cost_panel

st.set_page_config(
    page_title="HIPAA Readiness Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared styles ────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stSidebar"] { background-color: #0D0D15; }
  .stTabs [data-baseweb="tab-list"] { gap: 8px; }
  .stTabs [data-baseweb="tab"] {
      background-color: #12121A;
      border-radius: 6px;
      padding: 6px 16px;
  }
  .badge-required {
      background: #7f1d1d; color: #fca5a5;
      padding: 2px 8px; border-radius: 12px;
      font-size: 11px; font-weight: 600;
  }
  .badge-addressable {
      background: #431407; color: #fdba74;
      padding: 2px 8px; border-radius: 12px;
      font-size: 11px; font-weight: 600;
  }
  .badge-implemented { background: #052e16; color: #86efac; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .badge-partial { background: #422006; color: #fde047; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .badge-notimpl { background: #1c1c1c; color: #9ca3af; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .metric-card {
      background: #12121A; border: 1px solid #1e1e2e;
      border-radius: 8px; padding: 16px;
  }
  .critical-flash { animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.6; } }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
DEFAULTS = {
    "org_name": "",
    "entity_type": "Business Associate",
    "ephi_systems": [],
    "ephi_leaves_org": True,
    "soc2_status": "None",
    "remote_workforce": False,
    "workforce_size": 50,
    "demo_mode": False,
    "assessment_run": False,
    "readiness_results": None,
    "claude_analysis": None,
    "baa_list": None,
    "roadmap": None,
    "connector_findings": {},
    "manual_overrides": {},
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar — org context ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 HIPAA Readiness Agent")
    st.caption("Security Rule Gap Assessment · BAA Tracking · SOC2 Overlap · Remediation")
    st.divider()

    demo = st.toggle("Demo Mode", value=st.session_state.demo_mode, key="demo_mode_toggle")
    if demo != st.session_state.demo_mode:
        st.session_state.demo_mode = demo
        if demo:
            # Load Meridian Health Tech demo context
            st.session_state.org_name = "Meridian Health Tech"
            st.session_state.entity_type = "Business Associate"
            st.session_state.ephi_systems = ["Cloud Storage", "EHR Integration API", "Billing System", "Internal Messaging"]
            st.session_state.ephi_leaves_org = True
            st.session_state.soc2_status = "Type I Complete"
            st.session_state.remote_workforce = True
            st.session_state.workforce_size = 150
        st.rerun()

    st.markdown("### Organization")
    st.session_state.org_name = st.text_input(
        "Organization Name",
        value=st.session_state.org_name,
        placeholder="Acme Health Co.",
    )
    st.session_state.entity_type = st.selectbox(
        "Entity Type",
        ["Covered Entity", "Business Associate", "Both"],
        index=["Covered Entity", "Business Associate", "Both"].index(
            st.session_state.entity_type
        ),
    )
    st.session_state.ephi_systems = st.multiselect(
        "ePHI Systems",
        ["EHR", "EHR Integration API", "Billing System", "Cloud Storage",
         "Internal Messaging", "Email", "Patient Portal", "Custom"],
        default=st.session_state.ephi_systems,
    )
    st.session_state.ephi_leaves_org = st.toggle(
        "ePHI leaves organization?",
        value=st.session_state.ephi_leaves_org,
    )

    st.markdown("### SOC2 & Workforce")
    st.session_state.soc2_status = st.selectbox(
        "SOC2 Status",
        ["None", "Type I in progress", "Type I Complete", "Type II Complete"],
        index=["None", "Type I in progress", "Type I Complete", "Type II Complete"].index(
            st.session_state.soc2_status
        ),
    )
    st.session_state.remote_workforce = st.toggle(
        "Remote Workforce?",
        value=st.session_state.remote_workforce,
    )
    st.session_state.workforce_size = st.number_input(
        "Workforce Size",
        min_value=1,
        max_value=100000,
        value=st.session_state.workforce_size,
        step=10,
    )

    if st.session_state.assessment_run and st.session_state.readiness_results:
        st.divider()
        score = st.session_state.readiness_results.get("overall", 0)
        band = st.session_state.readiness_results.get("band_label", "")
        color = st.session_state.readiness_results.get("band_color", "#6B7280")
        st.markdown(f"**Last Score:** <span style='color:{color}'>{score:.1f}% — {band}</span>", unsafe_allow_html=True)

    st.divider()
    render_cost_panel()

# ── Main page ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("# HIPAA Security Rule Readiness Agent")
    st.caption(
        "Full-lifecycle assessment across all 42 controls · Administrative · Physical · Technical"
    )

if st.session_state.demo_mode:
    st.info(
        "**Demo Mode Active** — Meridian Health Tech: 150-person SaaS Business Associate "
        "for 3 hospital EHR clients. SOC2 Type I complete. No BAA audit in 2 years.",
        icon="🎭"
    )

if not st.session_state.org_name:
    st.warning("Enter your organization name in the sidebar to begin, or enable Demo Mode.")
else:
    # Summary stats if assessment has run
    if st.session_state.assessment_run and st.session_state.readiness_results:
        r = st.session_state.readiness_results
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Overall Score", f"{r['overall']:.1f}%", delta=r['band_label'])
        c2.metric("Critical Gaps", len(r.get('critical_gaps', [])), delta="Required at 0%", delta_color="inverse")
        c3.metric("High Gaps", len(r.get('high_gaps', [])), delta_color="inverse")
        c4.metric("Controls Implemented", r.get('implemented_count', 0), f"of {r.get('total_controls', 42)}")
        baa_list = st.session_state.baa_list or []
        critical_baa = len([b for b in baa_list if b.get('risk_tier') == 'CRITICAL'])
        c5.metric("Critical BAA Gaps", critical_baa, delta_color="inverse")

        st.markdown("---")

    st.markdown("""
### Navigate the tabs above to:
| Tab | What you'll find |
|-----|-----------------|
| **Integrations** | Connect data sources or use Demo Mode |
| **Gap Assessment** | Score all 42 controls across 3 safeguard categories |
| **BAA Tracker** | Business Associate inventory with risk classification |
| **SOC2 Overlap** | Which HIPAA controls your SOC2 work already covers |
| **Remediation Roadmap** | Claude-generated phased action plan, exportable |
""")

    st.caption(
        "HIPAA Security Rule (45 CFR §164.300–.318) · "
        "This tool assists with readiness assessment and does not constitute legal advice."
    )
