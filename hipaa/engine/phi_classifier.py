"""
Determines ePHI scope from org inputs.
Used to weight certain controls higher in scoring context.
"""

EPHI_SYSTEM_WEIGHTS = {
    "EHR": {"weight": 1.5, "connectors": ["aws", "gcp", "azure"]},
    "EHR Integration API": {"weight": 1.5, "connectors": ["aws", "gcp"]},
    "Billing System": {"weight": 1.3, "connectors": ["aws", "manual"]},
    "Cloud Storage": {"weight": 1.2, "connectors": ["aws", "gcp", "azure"]},
    "Internal Messaging": {"weight": 1.1, "connectors": ["slack", "google_workspace"]},
    "Email": {"weight": 1.1, "connectors": ["google_workspace"]},
    "Patient Portal": {"weight": 1.4, "connectors": ["aws", "gcp"]},
    "Custom": {"weight": 1.0, "connectors": ["manual"]},
}

HIGH_RISK_CONTROLS_BY_SYSTEM = {
    "EHR": ["TEC-001", "TEC-004", "TEC-005", "TEC-007", "TEC-009", "ADM-001"],
    "EHR Integration API": ["TEC-001", "TEC-004", "TEC-005", "TEC-007", "TEC-008", "TEC-009"],
    "Billing System": ["ADM-022", "TEC-004", "TEC-005", "ADM-001"],
    "Cloud Storage": ["TEC-004", "PHY-007", "PHY-008", "ADM-016"],
    "Internal Messaging": ["TEC-009", "ADM-022"],
    "Email": ["TEC-009", "ADM-022"],
}


def classify_ephi_scope(org_context: dict) -> dict:
    systems = org_context.get("ephi_systems", [])
    remote = org_context.get("remote_workforce", False)
    ephi_leaves = org_context.get("ephi_leaves_org", False)

    # Determine highest-risk controls for this org
    high_risk_ids = set()
    for system in systems:
        for ctrl_id in HIGH_RISK_CONTROLS_BY_SYSTEM.get(system, []):
            high_risk_ids.add(ctrl_id)

    if remote:
        high_risk_ids.update(["PHY-005", "PHY-006", "TEC-003", "ADM-012"])

    if ephi_leaves:
        high_risk_ids.update(["ADM-022", "TEC-008", "TEC-009"])

    # Determine relevant connectors
    relevant_connectors = set()
    for system in systems:
        for conn in EPHI_SYSTEM_WEIGHTS.get(system, {}).get("connectors", []):
            relevant_connectors.add(conn)

    return {
        "systems": systems,
        "high_risk_control_ids": list(high_risk_ids),
        "relevant_connectors": list(relevant_connectors),
        "remote_workforce": remote,
        "ephi_leaves_org": ephi_leaves,
        "risk_multiplier": max(
            EPHI_SYSTEM_WEIGHTS.get(s, {}).get("weight", 1.0) for s in systems
        ) if systems else 1.0,
    }
