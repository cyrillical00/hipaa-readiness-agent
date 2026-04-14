"""
Claude API integration for generating phased HIPAA remediation roadmaps.
"""
import json
import os
import streamlit as st
import anthropic


def _get_client() -> anthropic.Anthropic:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured in secrets.")
    return anthropic.Anthropic(api_key=api_key)


def build_roadmap_prompt(
    control_results: dict,
    controls: list[dict],
    baa_summary: dict,
    overlap_analysis: dict,
    org_context: dict,
) -> str:
    critical_gaps = [
        f"- {r['control_id']}: {r['status']} (notes: {r.get('notes', 'N/A')})"
        for r in control_results.get("critical_gaps", [])
    ]
    high_gaps = [
        f"- {r['control_id']}: {r['status']} (notes: {r.get('notes', 'N/A')})"
        for r in control_results.get("high_gaps", [])
    ]

    control_map = {c["id"]: c for c in controls}
    critical_detail = []
    for r in control_results.get("critical_gaps", []):
        c = control_map.get(r["control_id"], {})
        critical_detail.append(
            f"- {r['control_id']} [{c.get('standard', '')} / {c.get('spec', '')}]: "
            f"Status={r['status']}, Effort={c.get('remediation_effort', 'Unknown')}, "
            f"Impact={c.get('remediation_impact', 'Unknown')}"
        )

    return f"""You are a HIPAA compliance expert. Generate a structured 3-phase remediation roadmap for the organization below.

## Organization Context
- Name: {org_context.get('org_name', 'Unknown')}
- Entity Type: {org_context.get('entity_type', 'Business Associate')}
- ePHI Systems: {', '.join(org_context.get('ephi_systems', []))}
- ePHI Leaves Org: {org_context.get('ephi_leaves_org', False)}
- SOC2 Status: {org_context.get('soc2_status', 'None')}
- Remote Workforce: {org_context.get('remote_workforce', False)}
- Workforce Size: {org_context.get('workforce_size', 'Unknown')}

## Current Readiness Score
- Overall: {control_results.get('overall', 0):.1f}% ({control_results.get('band_label', 'Unknown')})
- Administrative: {control_results.get('category_scores', {}).get('Administrative', 0):.1f}%
- Physical: {control_results.get('category_scores', {}).get('Physical', 0):.1f}%
- Technical: {control_results.get('category_scores', {}).get('Technical', 0):.1f}%

## Critical Gaps (Required Controls at 0%)
{chr(10).join(critical_detail) if critical_detail else "None"}

## High Priority Gaps
{chr(10).join(high_gaps) if high_gaps else "None"}

## BAA Risk Summary
- Total Business Associates: {baa_summary.get('total', 0)}
- ePHI Vendors: {baa_summary.get('ephi_vendors', 0)}
- Missing BAAs: {baa_summary.get('missing_baas', 0)} CRITICAL
- Expired BAAs: {baa_summary.get('expired', 0)} HIGH
- Expiring in 90 days: {baa_summary.get('expiring_90d', 0)} MEDIUM

## SOC2 Overlap
- Coverage: {overlap_analysis.get('coverage_pct', 0):.1f}% of HIPAA controls partially or fully covered by SOC2
- Full overlap controls: {overlap_analysis.get('full_overlap', 0)}
- Partial overlap controls: {overlap_analysis.get('partial_overlap', 0)}
- No SOC2 coverage: {overlap_analysis.get('no_overlap', 0)}

---

Generate a JSON response ONLY (no markdown, no explanation) with this exact structure:
{{
  "executive_summary": "2-3 sentence summary of overall HIPAA posture and top priority",
  "overall_risk_tier": "CRITICAL|HIGH|MEDIUM|LOW",
  "phases": [
    {{
      "phase": 1,
      "label": "0–30 Days: Critical Remediation",
      "description": "Brief phase description",
      "items": [
        {{
          "control_id": "ADM-022",
          "title": "Execute BAAs with Google Workspace and Slack",
          "description": "Detailed action description",
          "owner_role": "Legal / Compliance",
          "effort": "S|M|L",
          "priority": "CRITICAL|HIGH|MEDIUM",
          "expected_artifact": "Signed BAA on file",
          "soc2_reuse": true|false,
          "soc2_note": "Note if SOC2 evidence can be reused"
        }}
      ]
    }},
    {{
      "phase": 2,
      "label": "31–90 Days: Policy & Documentation",
      "description": "...",
      "items": [...]
    }},
    {{
      "phase": 3,
      "label": "91–180 Days: Audit Readiness",
      "description": "...",
      "items": [...]
    }}
  ],
  "quick_wins": [
    {{
      "control_id": "...",
      "title": "...",
      "description": "...",
      "effort": "S",
      "impact": "HIGH"
    }}
  ]
}}

Rules:
- Phase 1: Required controls at 0%, all CRITICAL BAA gaps, items that can be done in < 1 week
- Phase 2: Addressable controls, policy docs, training program, BAA renewals
- Phase 3: DR testing, audit prep, evidence packages, third-party assessment readiness
- Include at least 5 items per phase
- Quick wins must be small effort (S) with high or critical impact
- Be specific — name the exact vendor, system, or policy document needed
- Note where SOC2 Type I evidence can be directly reused
"""


def generate_roadmap(
    control_results: dict,
    controls: list[dict],
    baa_summary: dict,
    overlap_analysis: dict,
    org_context: dict,
    stream_placeholder=None,
) -> dict:
    """Call Claude to generate roadmap. Returns parsed JSON dict."""
    client = _get_client()
    prompt = build_roadmap_prompt(
        control_results, controls, baa_summary, overlap_analysis, org_context
    )

    full_text = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=(
            "You are a HIPAA Security Rule compliance expert. You generate precise, actionable "
            "remediation roadmaps. Always respond with valid JSON only — no markdown code blocks, "
            "no preamble, no explanation. Output must be parseable by json.loads()."
        ),
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            if stream_placeholder:
                stream_placeholder.text(f"Generating roadmap... {len(full_text)} chars")

    # Clean up any accidental markdown fencing
    cleaned = full_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    return json.loads(cleaned)


def score_assessment_with_claude(
    control_statuses: dict,
    controls: list[dict],
    connector_findings: dict,
    org_context: dict,
    stream_placeholder=None,
) -> dict:
    """
    Claude call #1: scores controls, flags gaps, classifies risk tiers.
    Returns structured gap analysis JSON.
    """
    client = _get_client()

    control_map = {c["id"]: c for c in controls}
    control_summary = []
    for ctrl_id, status_info in control_statuses.items():
        c = control_map.get(ctrl_id, {})
        control_summary.append(
            f"- {ctrl_id} [{c.get('safeguard', '')} / {c.get('spec', '')}] "
            f"({c.get('status', '')}): {status_info.get('status', 'Unknown')} | "
            f"Evidence: {status_info.get('evidence', False)} | Notes: {status_info.get('notes', '')}"
        )

    prompt = f"""You are a HIPAA Security Rule auditor. Analyze this organization's control assessment.

## Organization
- Name: {org_context.get('org_name', 'Unknown')}
- Entity Type: {org_context.get('entity_type', 'Business Associate')}
- SOC2 Status: {org_context.get('soc2_status', 'None')}
- ePHI Systems: {', '.join(org_context.get('ephi_systems', []))}

## Control Assessment ({len(control_statuses)} controls)
{chr(10).join(control_summary)}

Return valid JSON only:
{{
  "gap_summary": "2-sentence summary of overall gaps",
  "overall_risk_tier": "CRITICAL|HIGH|MEDIUM|LOW",
  "critical_gaps": [
    {{"control_id": "...", "reason": "...", "immediate_action": "..."}}
  ],
  "high_gaps": [
    {{"control_id": "...", "reason": "...", "recommended_action": "..."}}
  ],
  "quick_wins": [
    {{"control_id": "...", "action": "...", "effort_days": 1}}
  ],
  "audit_exposure": "What an auditor would flag first",
  "positive_findings": ["List of controls that are well-implemented"]
}}"""

    full_text = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=(
            "You are a HIPAA Security Rule auditor. Respond with valid JSON only — no markdown, "
            "no preamble. Output must be parseable by json.loads()."
        ),
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            if stream_placeholder:
                stream_placeholder.text(f"Analyzing controls... {len(full_text)} chars")

    cleaned = full_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    return json.loads(cleaned)
