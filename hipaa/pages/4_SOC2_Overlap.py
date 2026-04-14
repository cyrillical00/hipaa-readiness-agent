"""
Tab 4 — SOC2 Overlap
Control crosswalk — what SOC2 work already covers HIPAA.
"""
import streamlit as st
import plotly.graph_objects as go
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.soc2_crosswalk import load_crosswalk, compute_overlap
from engine.control_mapper import load_controls

st.set_page_config(page_title="SOC2 Overlap — HIPAA Agent", layout="wide")
st.markdown("# SOC2 → HIPAA Control Overlap")
st.caption(
    "If your organization has completed SOC2, many HIPAA Security Rule controls "
    "may already be satisfied. This tab shows exactly which ones and what evidence you can reuse."
)

controls = load_controls()
ctrl_map = {c["id"]: c for c in controls}
crosswalk = load_crosswalk()
soc2_status = st.session_state.get("soc2_status", "None")

overlap = compute_overlap(crosswalk, soc2_status)

# ── Key callout ───────────────────────────────────────────────────────────────
if soc2_status in ("Type I Complete", "Type II Complete"):
    st.success(
        f"**SOC2 {soc2_status}** — Based on your crosswalk, approximately "
        f"**{overlap['coverage_pct']:.0f}%** of HIPAA Security Rule controls are fully or partially "
        f"satisfied by your existing SOC2 work. "
        f"{overlap['full_overlap']} controls have full evidence reuse · "
        f"{overlap['partial_overlap']} need supplemental HIPAA-specific documentation.",
        icon="✅"
    )
elif soc2_status == "Type I in progress":
    st.info(
        f"**SOC2 Type I in progress** — When complete, you may cover up to "
        f"~{overlap['coverage_pct']:.0f}% of HIPAA controls. Overlapping controls shown as 'Potential'.",
        icon="⏳"
    )
else:
    st.warning(
        "**No SOC2 program** — Overlaps shown are potential coverage if you pursue SOC2. "
        "Starting a SOC2 program is one of the highest-leverage investments for HIPAA readiness.",
        icon="💡"
    )

# ── Summary metrics ───────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Full Overlap", overlap["full_overlap"], delta="Evidence directly reusable")
c2.metric("Partial Overlap", overlap["partial_overlap"], delta="Supplemental docs needed")
c3.metric("No Overlap", overlap["no_overlap"], delta="HIPAA-specific work required", delta_color="inverse")
c4.metric("Coverage", f"{overlap['coverage_pct']:.0f}%")

st.divider()

# ── Stacked bar by safeguard ──────────────────────────────────────────────────
cat_stats = overlap["category_stats"]
categories = list(cat_stats.keys())

if soc2_status != "None":
    full_vals = [cat_stats[c]["full"] for c in categories]
    partial_vals = [cat_stats[c]["partial"] for c in categories]
    none_vals = [cat_stats[c]["none"] for c in categories]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Full Overlap", x=categories, y=full_vals,
        marker_color="#22C55E", text=full_vals, textposition="inside",
    ))
    fig.add_trace(go.Bar(
        name="Partial Overlap", x=categories, y=partial_vals,
        marker_color="#EAB308", text=partial_vals, textposition="inside",
    ))
    fig.add_trace(go.Bar(
        name="HIPAA-Only (No SOC2)", x=categories, y=none_vals,
        marker_color="#6B7280", text=none_vals, textposition="inside",
    ))
    fig.update_layout(
        barmode="stack",
        paper_bgcolor="#0A0A0F",
        plot_bgcolor="#0A0A0F",
        font_color="#E2E8F0",
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(gridcolor="#1e1e2e"),
        yaxis=dict(gridcolor="#1e1e2e"),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Set your SOC2 status in the sidebar to see coverage analysis.")

st.divider()

# ── Two-column crosswalk view ─────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

OVERLAP_COLORS = {
    "Full": ("#22C55E", "#052e16"),
    "Partial": ("#EAB308", "#422006"),
    "None": ("#6B7280", "#1c1c1c"),
}

with col_left:
    st.markdown("### Control-by-Control Crosswalk")

    # Filter
    filter_col1, filter_col2 = st.columns(2)
    safeguard_filter = filter_col1.selectbox(
        "Safeguard", ["All", "Administrative", "Physical", "Technical"],
        key="soc2_safeguard_filter"
    )
    overlap_filter = filter_col2.selectbox(
        "Overlap Type", ["All", "Full", "Partial", "None"],
        key="soc2_overlap_filter"
    )

    items = overlap["items"]
    if safeguard_filter != "All":
        prefix = {"Administrative": "ADM", "Physical": "PHY", "Technical": "TEC"}[safeguard_filter]
        items = [i for i in items if i["hipaa_id"].startswith(prefix)]
    if overlap_filter != "All":
        items = [i for i in items if overlap_filter.lower() in i["effective_overlap"].lower()]

    for item in items:
        eff = item["effective_overlap"]
        if "Full" in eff:
            color, bg = OVERLAP_COLORS["Full"]
        elif "Partial" in eff or "Potential" in eff:
            color, bg = OVERLAP_COLORS["Partial"]
        else:
            color, bg = OVERLAP_COLORS["None"]

        ctrl = ctrl_map.get(item["hipaa_id"], {})
        criteria_str = ", ".join(item["soc2_criteria"]) if item["soc2_criteria"] else "—"

        st.markdown(
            f"<div style='background:{bg};border:1px solid #1e1e2e;border-left:4px solid {color};"
            f"padding:10px 14px;border-radius:6px;margin-bottom:6px'>"
            f"<div style='display:flex;justify-content:space-between'>"
            f"<strong style='color:#E2E8F0'>{item['hipaa_id']}</strong> "
            f"<span style='color:{color};font-size:12px;font-weight:700'>{eff}</span>"
            f"</div>"
            f"<div style='color:#94a3b8;font-size:13px'>{ctrl.get('standard', '')} / {item['hipaa_spec']}</div>"
            f"<div style='margin-top:4px'>"
            f"<span style='color:#6366F1;font-size:12px'>SOC2: {criteria_str}</span>"
            f"</div>"
            f"<div style='color:#64748b;font-size:12px;margin-top:4px;font-style:italic'>{item['notes']}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

with col_right:
    st.markdown("### Overlap Summary")

    for cat in ["Administrative", "Physical", "Technical"]:
        stats = cat_stats[cat]
        total = stats["total"]
        full = stats["full"]
        partial = stats["partial"]
        none = stats["none"]

        st.markdown(
            f"<div style='background:#12121A;border:1px solid #1e1e2e;padding:12px;"
            f"border-radius:6px;margin-bottom:8px'>"
            f"<strong style='color:#E2E8F0'>{cat}</strong>"
            f"<div style='margin-top:8px'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:2px'>"
            f"<span style='color:#22C55E;font-size:12px'>Full overlap</span>"
            f"<span style='color:#22C55E;font-size:12px'>{full}/{total}</span></div>"
            f"<div style='background:#1e1e2e;border-radius:4px;height:6px'>"
            f"<div style='background:#22C55E;width:{full/total*100:.0f}%;height:6px;border-radius:4px'></div></div>"
            f"<div style='display:flex;justify-content:space-between;margin-top:4px;margin-bottom:2px'>"
            f"<span style='color:#EAB308;font-size:12px'>Partial overlap</span>"
            f"<span style='color:#EAB308;font-size:12px'>{partial}/{total}</span></div>"
            f"<div style='background:#1e1e2e;border-radius:4px;height:6px'>"
            f"<div style='background:#EAB308;width:{partial/total*100:.0f}%;height:6px;border-radius:4px'></div></div>"
            f"<div style='display:flex;justify-content:space-between;margin-top:4px;margin-bottom:2px'>"
            f"<span style='color:#6B7280;font-size:12px'>HIPAA-only</span>"
            f"<span style='color:#6B7280;font-size:12px'>{none}/{total}</span></div>"
            f"<div style='background:#1e1e2e;border-radius:4px;height:6px'>"
            f"<div style='background:#6B7280;width:{none/total*100:.0f}%;height:6px;border-radius:4px'></div></div>"
            f"</div></div>",
            unsafe_allow_html=True
        )

    st.divider()
    st.markdown("#### HIPAA-Only Controls (No SOC2 Coverage)")
    st.caption("These require net-new work regardless of SOC2 status.")
    hipaa_only = [i for i in overlap["items"] if i["effective_overlap"] == "None"]
    for item in hipaa_only:
        ctrl = ctrl_map.get(item["hipaa_id"], {})
        st.markdown(
            f"<div style='padding:6px 0;border-left:3px solid #6B7280;padding-left:10px;margin-bottom:4px'>"
            f"<strong style='color:#E2E8F0'>{item['hipaa_id']}</strong> "
            f"<span style='color:#94a3b8;font-size:13px'>— {item['hipaa_spec']}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
