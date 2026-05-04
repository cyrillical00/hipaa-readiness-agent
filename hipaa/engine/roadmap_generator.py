"""Claude API integration for generating phased HIPAA remediation roadmaps."""
from engine.claude_client import ClaudeWrapper


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

___

Generate a JSON response ONLY (no markdown, no explanation) with this exact structure:
{{
  "executive_summary": "2-3 sentence summary of overall HIPAA posture and top priority",
  "overall_risk_tier": "CRITICAL|HIGH|MEDIUM|LOW",
  "phases": [
    {{
      "phase": 1,
      "label": "0 to 30 Days: Critical Remediation",
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
      "label": "31 to 90 Days: Policy and Documentation",
      "description": "...",
      "items": [...]
    }},
    {{
      "phase": 3,
      "label": "91 to 180 Days: Audit Readiness",
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
- Phase 1: Required controls at 0%, all CRITICAL BAA gaps, items that can be done in under 1 week
- Phase 2: Addressable controls, policy docs, training program, BAA renewals
- Phase 3: DR testing, audit prep, evidence packages, third-party assessment readiness
- Include at least 5 items per phase
- Quick wins must be small effort (S) with high or critical impact
- Be specific. Name the exact vendor, system, or policy document needed.
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
    prompt = build_roadmap_prompt(
        control_results, controls, baa_summary, overlap_analysis, org_context
    )

    system_prompt = (
        "You are a HIPAA Security Rule compliance expert. You generate precise, actionable "
        "remediation roadmaps. Always respond with valid JSON only. No markdown code blocks, "
        "no preamble, no explanation. Output must be parseable by json.loads()."
    )

    wrapper = ClaudeWrapper(model="claude-sonnet-4-6")
    parsed, _ = wrapper.stream_json(
        system_prompt=system_prompt,
        user_prompt=prompt,
        max_tokens=4096,
        stream_placeholder=stream_placeholder,
        progress_label="Generating roadmap",
    )
    return parsed


def score_assessment_with_claude(
    control_statuses: dict,
    controls: list[dict],
    connector_findings: dict,
    org_context: dict,
    stream_placeholder=None,
) -> dict:
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

    system_prompt = (
        "You are a HIPAA Security Rule auditor. Respond with valid JSON only. No markdown, "
        "no preamble. Output must be parseable by json.loads()."
    )

    wrapper = ClaudeWrapper(model="claude-sonnet-4-6")
    parsed, _ = wrapper.stream_json(
        system_prompt=system_prompt,
        user_prompt=prompt,
        max_tokens=2048,
        stream_placeholder=stream_placeholder,
        progress_label="Analyzing controls",
    )
    return parsed
