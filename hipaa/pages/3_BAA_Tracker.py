"""
Tab 3 — BAA Tracker
Business Associate inventory with risk classification.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.baa_engine import enrich_baa_list, baa_summary, RISK_COLORS
from data.sample_baas import DEMO_BAAS
from utils.csv_exporter import export_baa_csv
from auth.login import require_login
require_login()

st.set_page_config(page_title="BAA Tracker — HIPAA Agent", layout="wide")
st.markdown("# Business Associate Agreement Tracker")
st.caption(
    "HIPAA §164.308(b) · BAAs are mandatory for any vendor with access to ePHI. "
    "Missing BAAs are the most common HIPAA enforcement finding."
)

# ── Initialize BAA list ───────────────────────────────────────────────────────
if "baa_list" not in st.session_state or st.session_state.baa_list is None:
    if st.session_state.get("demo_mode"):
        st.session_state.baa_list = enrich_baa_list(DEMO_BAAS)
    else:
        st.session_state.baa_list = []

# ── Demo mode auto-load ───────────────────────────────────────────────────────
if st.session_state.get("demo_mode") and not st.session_state.baa_list:
    st.session_state.baa_list = enrich_baa_list(DEMO_BAAS)

baas = st.session_state.baa_list

# ── Summary metrics row ───────────────────────────────────────────────────────
if baas:
    summary = baa_summary(baas)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total BAs", summary["total"])
    c2.metric("ePHI Vendors", summary["ephi_vendors"])
    c3.metric(
        "Missing BAAs",
        summary["missing_baas"],
        delta="CRITICAL" if summary["missing_baas"] > 0 else "Clear",
        delta_color="inverse" if summary["missing_baas"] > 0 else "normal",
    )
    c4.metric(
        "Expired BAAs",
        summary["expired"],
        delta="HIGH" if summary["expired"] > 0 else "Clear",
        delta_color="inverse" if summary["expired"] > 0 else "normal",
    )
    c5.metric(
        "Expiring in 90d",
        summary["expiring_90d"],
        delta_color="off",
    )
    c6.metric("BAA Compliance", f"{summary['compliance_rate']:.0f}%")

    # ── Donut chart ───────────────────────────────────────────────────────────
    tier_counts = {
        "CRITICAL": len([b for b in baas if b["risk_tier"] == "CRITICAL"]),
        "HIGH": len([b for b in baas if b["risk_tier"] == "HIGH"]),
        "MEDIUM": len([b for b in baas if b["risk_tier"] == "MEDIUM"]),
        "LOW": len([b for b in baas if b["risk_tier"] == "LOW"]),
    }

    col_donut, col_info = st.columns([2, 3])
    with col_donut:
        fig = go.Figure(go.Pie(
            labels=list(tier_counts.keys()),
            values=list(tier_counts.values()),
            hole=0.6,
            marker_colors=["#DC2626", "#F97316", "#EAB308", "#22C55E"],
            textinfo="label+value",
            textfont_color="#E2E8F0",
        ))
        fig.update_layout(
            paper_bgcolor="#0A0A0F",
            font_color="#E2E8F0",
            height=250,
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_info:
        st.markdown("#### Risk Classification Guide")
        risk_guide = [
            ("🔴 CRITICAL", "#DC2626", "ePHI shared + no BAA in place — immediate action required"),
            ("🟠 HIGH", "#F97316", "BAA in place but expired, or missing breach notification clause"),
            ("🟡 MEDIUM", "#EAB308", "BAA complete but sub-contractors not disclosed"),
            ("🟢 LOW", "#22C55E", "Fully compliant BAA on file"),
        ]
        for tier, color, desc in risk_guide:
            st.markdown(
                f"<div style='padding:6px 0;border-left:3px solid {color};padding-left:10px;margin-bottom:4px'>"
                f"<strong style='color:{color}'>{tier}</strong> — <span style='color:#94a3b8;font-size:13px'>{desc}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    st.divider()

    # ── Filter controls ───────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    tier_filter = col_f1.selectbox("Filter by Risk Tier", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    ephi_filter = col_f2.selectbox("ePHI Filter", ["All", "ePHI Shared", "No ePHI"])
    baa_filter = col_f3.selectbox("BAA Status", ["All", "BAA In Place", "Missing BAA"])

    filtered = baas
    if tier_filter != "All":
        filtered = [b for b in filtered if b["risk_tier"] == tier_filter]
    if ephi_filter == "ePHI Shared":
        filtered = [b for b in filtered if b.get("ephi_shared")]
    elif ephi_filter == "No ePHI":
        filtered = [b for b in filtered if not b.get("ephi_shared")]
    if baa_filter == "BAA In Place":
        filtered = [b for b in filtered if b.get("baa_in_place")]
    elif baa_filter == "Missing BAA":
        filtered = [b for b in filtered if not b.get("baa_in_place")]

    st.markdown(f"### Business Associates ({len(filtered)} shown)")

    # ── BAA cards ─────────────────────────────────────────────────────────────
    for baa in sorted(filtered, key=lambda b: ["CRITICAL", "HIGH", "MEDIUM", "LOW"].index(b["risk_tier"])):
        risk_color = RISK_COLORS[baa["risk_tier"]]
        vendor = baa.get("vendor", "Unknown")
        days = baa.get("days_until_review")

        if days is not None and days < 0:
            days_str = f"<span style='color:#DC2626'>EXPIRED {abs(days)} days ago</span>"
        elif days is not None and days <= 90:
            days_str = f"<span style='color:#EAB308'>{days} days until review</span>"
        elif days is not None:
            days_str = f"<span style='color:#22C55E'>{days} days until review</span>"
        else:
            days_str = "<span style='color:#6B7280'>No review date</span>"

        ephi_badge = (
            "<span style='background:#450a0a;color:#fca5a5;padding:2px 8px;border-radius:12px;font-size:11px'>ePHI</span>"
            if baa.get("ephi_shared") else
            "<span style='background:#1c1c1c;color:#6B7280;padding:2px 8px;border-radius:12px;font-size:11px'>No ePHI</span>"
        )
        baa_status_badge = (
            "<span style='background:#052e16;color:#86efac;padding:2px 8px;border-radius:12px;font-size:11px'>BAA ✓</span>"
            if baa.get("baa_in_place") else
            "<span style='background:#450a0a;color:#fca5a5;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700'>NO BAA</span>"
        )

        with st.container():
            st.markdown(
                f"<div style='background:#12121A;border:1px solid #1e1e2e;"
                f"border-left:4px solid {risk_color};"
                f"padding:14px 16px;border-radius:6px;margin-bottom:8px'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center'>"
                f"<div>"
                f"<strong style='color:#E2E8F0;font-size:15px'>{vendor}</strong> "
                f"{ephi_badge} {baa_status_badge}"
                f"</div>"
                f"<div style='text-align:right'>"
                f"<span style='color:{risk_color};font-size:13px;font-weight:700'>{baa['risk_badge']}</span>"
                f"</div></div>"
                f"<div style='color:#94a3b8;font-size:12px;margin-top:6px'>"
                f"{baa.get('services', '')} &nbsp;·&nbsp; {days_str}"
                f"</div>",
                unsafe_allow_html=True
            )

            with st.expander(f"Details — {vendor}"):
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"**ePHI Shared:** {'Yes' if baa.get('ephi_shared') else 'No'}")
                col1.markdown(f"**BAA in Place:** {'Yes' if baa.get('baa_in_place') else '❌ No'}")
                col1.markdown(f"**Signed Date:** {baa.get('baa_signed_date') or '—'}")
                col2.markdown(f"**Review Date:** {baa.get('baa_review_date') or '—'}")
                col2.markdown(f"**Sub-BAs Disclosed:** {'Yes' if baa.get('sub_bas_disclosed') else 'No'}")
                col2.markdown(f"**Breach Clause:** {'Yes' if baa.get('security_incident_clause') else '❌ No'}")
                col3.markdown(f"**Breach Window:** {baa.get('breach_notification_window', 'not specified')}")
                if baa.get("notes"):
                    st.markdown(f"*{baa['notes']}*")

            st.markdown("</div>", unsafe_allow_html=True)

    # ── Export ────────────────────────────────────────────────────────────────
    st.divider()
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        csv_data = export_baa_csv(baas)
        st.download_button(
            "Download BAA Inventory CSV",
            data=csv_data,
            file_name="baa_inventory.csv",
            mime="text/csv",
        )

else:
    # No BAAs loaded — show add form
    st.info("No BAA inventory loaded. Enable Demo Mode or add vendors below.")

# ── Add BAA form ──────────────────────────────────────────────────────────────
st.divider()
st.markdown("### Add / Import Business Associates")

add_tab, upload_tab = st.tabs(["Add Single Vendor", "Upload CSV"])

with add_tab:
    with st.form("add_baa_form"):
        col1, col2 = st.columns(2)
        vendor_name = col1.text_input("Vendor / BA Name *")
        services = col2.text_input("Services Provided")
        col3, col4 = st.columns(2)
        ephi_shared = col3.toggle("ePHI Shared?", value=True)
        baa_in_place = col4.toggle("BAA in Place?", value=False)
        col5, col6 = st.columns(2)
        signed_date = col5.date_input("BAA Signed Date", value=None)
        review_date = col6.date_input("BAA Review Date", value=None)
        col7, col8 = st.columns(2)
        sub_bas = col7.toggle("Sub-BAs Disclosed?", value=False)
        breach_clause = col8.toggle("Security Incident Clause?", value=False)
        breach_window = st.selectbox(
            "Breach Notification Window",
            ["not specified", "24h", "48h", "60 days"],
        )
        notes = st.text_area("Notes", height=60)
        submitted = st.form_submit_button("Add Vendor", type="primary")

        if submitted and vendor_name:
            new_entry = {
                "vendor": vendor_name,
                "services": services,
                "ephi_shared": ephi_shared,
                "baa_in_place": baa_in_place,
                "baa_signed_date": signed_date.isoformat() if signed_date else None,
                "baa_review_date": review_date.isoformat() if review_date else None,
                "sub_bas_disclosed": sub_bas,
                "security_incident_clause": breach_clause,
                "breach_notification_window": breach_window,
                "notes": notes,
            }
            enriched = enrich_baa_list([new_entry])
            current = st.session_state.baa_list or []
            st.session_state.baa_list = current + enriched
            st.success(f"Added {vendor_name} — Risk Tier: {enriched[0]['risk_tier']}")
            st.rerun()

with upload_tab:
    st.caption("Upload a CSV matching the BAA inventory format. Download a template from the export button above.")
    uploaded = st.file_uploader("Upload BAA CSV", type=["csv"])
    if uploaded:
        try:
            df = pd.read_csv(io.BytesIO(uploaded.read()))
            records = df.to_dict("records")
            enriched = enrich_baa_list(records)
            st.session_state.baa_list = enriched
            st.success(f"Loaded {len(enriched)} BAA entries.")
            st.rerun()
        except Exception as e:
            st.error(f"Parse error: {e}")
