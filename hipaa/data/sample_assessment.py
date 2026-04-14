"""
Demo org: Meridian Health Tech
150-person SaaS company, Business Associate for 3 hospital EHR clients
60% remote workforce, SOC2 Type I complete, no BAA audit in 2 years.
Overall score designed to land ~58% (Partial Readiness).
"""

DEMO_ORG_CONTEXT = {
    "org_name": "Meridian Health Tech",
    "entity_type": "Business Associate",
    "ephi_systems": ["Cloud Storage", "EHR Integration API", "Billing System", "Internal Messaging"],
    "ephi_leaves_org": True,
    "soc2_status": "Type I Complete",
    "remote_workforce": True,
    "workforce_size": 150,
    "ephi_volume": "High",
    "industry": "Health IT / SaaS",
    "description": "150-person SaaS company providing EHR integration middleware for 3 hospital clients. Acts as Business Associate under all three agreements. SOC2 Type I completed 14 months ago. No BAA audit since initial contracts were signed 2 years ago.",
}

# Control statuses: maps control_id → {status, evidence, alt_control_documented (for Addressable)}
DEMO_CONTROL_STATUSES = {
    # Administrative — Required
    "ADM-001": {"status": "Partial", "evidence": True, "notes": "Risk analysis completed 3 years ago; not updated after cloud migration."},
    "ADM-002": {"status": "Partial", "evidence": True, "notes": "Risk register exists but several identified items are unmitigated."},
    "ADM-003": {"status": "Implemented", "evidence": True, "notes": "Sanction policy in employee handbook, last reviewed 8 months ago."},
    "ADM-004": {"status": "Partial", "evidence": False, "notes": "Logs exist in CloudTrail and Okta but no formal review procedure or cadence."},
    "ADM-005": {"status": "Implemented", "evidence": True, "notes": "VP of Engineering designated as Security Officer (informal, no formal appointment doc)."},
    "ADM-015": {"status": "Partial", "evidence": True, "notes": "Incident response plan exists from SOC2 audit. No ePHI breach notification procedure."},
    "ADM-016": {"status": "Implemented", "evidence": True, "notes": "AWS S3 backups configured with daily snapshots."},
    "ADM-017": {"status": "Partial", "evidence": True, "notes": "DR plan documented but never tested in a tabletop exercise."},
    "ADM-018": {"status": "Partial", "evidence": False, "notes": "Emergency mode procedures not documented for ePHI systems specifically."},
    "ADM-021": {"status": "Not Implemented", "evidence": False, "notes": "No formal HIPAA evaluation performed since initial compliance review."},
    "ADM-022": {"status": "Partial", "evidence": False, "notes": "BAAs exist for primary hospital clients but 3 sub-vendors with ePHI access have no BAAs."},

    # Administrative — Addressable
    "ADM-006": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Access authorization tied to Okta role assignments."},
    "ADM-007": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Background checks run on hire; periodic access reviews quarterly."},
    "ADM-008": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Offboarding checklist includes immediate Okta deprovisioning."},
    "ADM-009": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Access requests managed via Jira tickets with manager approval."},
    "ADM-010": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Quarterly access review process documented and executed."},
    "ADM-011": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Monthly Slack security reminders sent informally. No policy or tracking."},
    "ADM-012": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "CrowdStrike deployed on all managed endpoints."},
    "ADM-013": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Okta has login alerts but no formal monitoring procedure."},
    "ADM-014": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Password policy enforced via Okta: 12 char min, MFA required."},
    "ADM-019": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "DR plan has never been tested. No tabletop or failover exercise on record."},
    "ADM-020": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Systems classified in SOC2 scope but no ePHI-specific criticality matrix."},
    "ADM-023": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No documented annual HIPAA training program. Ad hoc onboarding mentions HIPAA briefly."},

    # Physical — Required
    "PHY-005": {"status": "Implemented", "evidence": True, "notes": "Acceptable use policy covers workstations. Remote work addendum added last year."},
    "PHY-006": {"status": "Partial", "evidence": False, "notes": "Screen lock enforced on managed devices. 40% of remote workers use personal BYOD devices."},
    "PHY-007": {"status": "Implemented", "evidence": True, "notes": "Data disposal procedure documented; hardware vendor provides certificates of destruction."},
    "PHY-008": {"status": "Implemented", "evidence": True, "notes": "Media sanitization policy in place; NIST 800-88 referenced."},

    # Physical — Addressable
    "PHY-001": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Cloud-primary org; primary facility has badge access. DR documented in BCP."},
    "PHY-002": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Office has physical security but no formal written Facility Security Plan."},
    "PHY-003": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Badge access exists; no documented role-based physical access matrix."},
    "PHY-004": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No formal maintenance log for physical systems in ePHI environment."},
    "PHY-009": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No formal device/media movement tracking. Jamf manages macOS fleet but no movement log."},
    "PHY-010": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "AWS backup procedures cover cloud storage. Physical media rarely moved."},

    # Technical — Required
    "TEC-001": {"status": "Implemented", "evidence": True, "notes": "All users have unique Okta IDs. No shared accounts detected in last audit."},
    "TEC-002": {"status": "Implemented", "evidence": True, "notes": "Break-glass AWS account documented and tested annually."},
    "TEC-005": {"status": "Partial", "evidence": True, "notes": "CloudTrail and Okta logs enabled. Retention set to 90 days (HIPAA guidance suggests 6 years)."},
    "TEC-007": {"status": "Implemented", "evidence": True, "notes": "Okta MFA enforced for all users including contractors."},

    # Technical — Addressable
    "TEC-003": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "15-minute screen lock enforced via Okta and MDM."},
    "TEC-004": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "S3 SSE-AES256 enabled. RDS encrypted at rest with AWS KMS."},
    "TEC-006": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Database checksums enabled but no formal integrity verification process for ePHI exports."},
    "TEC-008": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "TLS 1.2+ enforced on all API endpoints."},
    "TEC-009": {"status": "Partial", "evidence": False, "alt_documented": False, "notes": "APIs use TLS but internal email (Google Workspace) not confirmed for opportunistic TLS enforcement on all routes."},
}
