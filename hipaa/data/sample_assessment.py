"""
Demo org: Meridian Health Tech
150-person SaaS company, Business Associate for 3 hospital EHR clients
60% remote workforce, SOC2 Type I complete, no BAA audit in 2 years.
Phase 7 catalog expansion (62 controls): overall lands in the Partial band, with
Privacy and Breach Notification dragging the average since Meridian, as a BA,
has not built standalone Privacy Rule or Breach Notification programs.
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

# Control statuses: maps control_id to {status, evidence, alt_documented (for Addressable)}
DEMO_CONTROL_STATUSES = {
    # Administrative, Required
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

    # Administrative, Addressable
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

    # Physical, Required
    "PHY-005": {"status": "Implemented", "evidence": True, "notes": "Acceptable use policy covers workstations. Remote work addendum added last year."},
    "PHY-006": {"status": "Partial", "evidence": False, "notes": "Screen lock enforced on managed devices. 40% of remote workers use personal BYOD devices."},
    "PHY-007": {"status": "Implemented", "evidence": True, "notes": "Data disposal procedure documented; hardware vendor provides certificates of destruction."},
    "PHY-008": {"status": "Implemented", "evidence": True, "notes": "Media sanitization policy in place; NIST 800-88 referenced."},

    # Physical, Addressable
    "PHY-001": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Cloud-primary org; primary facility has badge access. DR documented in BCP."},
    "PHY-002": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Office has physical security but no formal written Facility Security Plan."},
    "PHY-003": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Badge access exists; no documented role-based physical access matrix."},
    "PHY-004": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No formal maintenance log for physical systems in ePHI environment."},
    "PHY-009": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No formal device/media movement tracking. Jamf manages macOS fleet but no movement log."},
    "PHY-010": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "AWS backup procedures cover cloud storage. Physical media rarely moved."},

    # Technical, Required
    "TEC-001": {"status": "Implemented", "evidence": True, "notes": "All users have unique Okta IDs. No shared accounts detected in last audit."},
    "TEC-002": {"status": "Implemented", "evidence": True, "notes": "Break-glass AWS account documented and tested annually."},
    "TEC-005": {"status": "Partial", "evidence": True, "notes": "CloudTrail and Okta logs enabled. Retention set to 90 days (HIPAA guidance suggests 6 years)."},
    "TEC-007": {"status": "Implemented", "evidence": True, "notes": "Okta MFA enforced for all users including contractors."},

    # Technical, Addressable
    "TEC-003": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "15-minute screen lock enforced via Okta and MDM."},
    "TEC-004": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "S3 SSE-AES256 enabled. RDS encrypted at rest with AWS KMS."},
    "TEC-006": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Database checksums enabled but no formal integrity verification process for ePHI exports."},
    "TEC-008": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "TLS 1.2+ enforced on all API endpoints."},
    "TEC-009": {"status": "Partial", "evidence": False, "alt_documented": False, "notes": "APIs use TLS but internal email (Google Workspace) not confirmed for opportunistic TLS enforcement on all routes."},

    # Privacy Rule (Phase 7), Meridian is a BA so most flow through CE contracts or are outright gaps
    "PRV-001": {"status": "Not Implemented", "evidence": False, "notes": "No Notice of Privacy Practices. As a BA, Meridian relies on the Covered Entity NPP but has not documented this dependency."},
    "PRV-002": {"status": "Not Implemented", "evidence": False, "notes": "No documented procedure for individual access requests; no escalation path back to the Covered Entity."},
    "PRV-003": {"status": "Not Implemented", "evidence": False, "notes": "No amendment request handling procedure documented."},
    "PRV-004": {"status": "Not Implemented", "evidence": False, "notes": "No disclosure accounting log maintained for non TPO disclosures."},
    "PRV-005": {"status": "N/A (Documented)", "evidence": True, "notes": "Privacy obligations flow through Covered Entity contracts; documented in BAA."},
    "PRV-006": {"status": "N/A (Documented)", "evidence": True, "notes": "Privacy obligations flow through Covered Entity contracts; documented in BAA."},
    "PRV-007": {"status": "Partial", "evidence": False, "notes": "Role based access in Okta limits ePHI exposure; no formal minimum necessary policy or routine disclosure protocol."},
    "PRV-008": {"status": "N/A (Documented)", "evidence": True, "notes": "Privacy obligations flow through Covered Entity contracts; documented in BAA."},
    "PRV-009": {"status": "N/A (Documented)", "evidence": True, "notes": "Privacy obligations flow through Covered Entity contracts; documented in BAA."},
    "PRV-010": {"status": "Not Implemented", "evidence": False, "notes": "No marketing policy documented. Meridian does not run patient marketing today; policy still required."},
    "PRV-011": {"status": "Not Implemented", "evidence": False, "notes": "No sale of PHI policy documented."},
    "PRV-012": {"status": "Not Implemented", "evidence": False, "notes": "No designated Privacy Officer. Security Officer informally fields privacy questions."},
    "PRV-013": {"status": "Partial", "evidence": False, "notes": "Onboarding mentions HIPAA briefly; no Privacy Rule specific curriculum or retraining cadence."},

    # Breach Notification (Phase 7), BA-specific obligations are the priority
    "BRN-001": {"status": "Partial", "evidence": False, "notes": "Incident response covers triage; no formal four factor breach risk assessment template or decision log."},
    "BRN-002": {"status": "Not Implemented", "evidence": False, "notes": "No individual notification template, content checklist, or delivery procedure."},
    "BRN-003": {"status": "Not Implemented", "evidence": False, "notes": "No media notification procedure. Threshold trigger (500+ residents per state) not flagged in incident playbook."},
    "BRN-004": {"status": "Not Implemented", "evidence": False, "notes": "No HHS submission procedure documented; no annual breach log maintained."},
    "BRN-005": {"status": "Partial", "evidence": False, "notes": "BAAs reference 60 day notification; no internal procedure, template, or affected individual identification workflow for BA to CE notice."},
    "BRN-006": {"status": "Not Implemented", "evidence": False, "notes": "No breach decision documentation log; no six year retention policy mapped to breach records."},
    "BRN-007": {"status": "Not Implemented", "evidence": False, "notes": "No standalone breach response plan. Relies on generic SOC2 incident plan with no breach specific roles, escalation, or notification ownership."},
}

# Pre-computed assessment results matching engine.scorer.compute_readiness shape.
# Phase 7: 62 control catalog (Security Rule + Privacy Rule + Breach Notification).
# Per-category scores include the new Privacy and Breach Notification safeguards.
DEMO_ASSESSMENT_RESULTS = {
    "overall": 57.6,
    "band_label": "Partial",
    "band_color": "#EAB308",
    "category_scores": {
        "Administrative": 66.5,
        "Physical": 67.0,
        "Technical": 85.6,
        "Privacy": 38.5,
        "Breach Notification": 14.3,
    },
    "total_controls": 62,
    "implemented_count": 21,
    "partial_count": 17,
    "not_implemented_count": 24,
    "critical_gaps": [
        {"control_id": "ADM-021", "status": "Not Implemented", "notes": "No periodic HIPAA evaluation since initial review."},
        {"control_id": "BRN-002", "status": "Not Implemented", "notes": "No individual breach notification template or procedure."},
        {"control_id": "BRN-003", "status": "Not Implemented", "notes": "No media notification procedure for 500+ resident breaches."},
        {"control_id": "BRN-004", "status": "Not Implemented", "notes": "No HHS Secretary notification procedure."},
        {"control_id": "BRN-006", "status": "Not Implemented", "notes": "No breach decision documentation log; no six year retention."},
        {"control_id": "BRN-007", "status": "Not Implemented", "notes": "No standalone breach response plan."},
        {"control_id": "PRV-001", "status": "Not Implemented", "notes": "No Notice of Privacy Practices documented."},
        {"control_id": "PRV-002", "status": "Not Implemented", "notes": "No procedure to handle individual access requests."},
        {"control_id": "PRV-003", "status": "Not Implemented", "notes": "No amendment request handling procedure."},
        {"control_id": "PRV-004", "status": "Not Implemented", "notes": "No disclosure accounting log."},
        {"control_id": "PRV-010", "status": "Not Implemented", "notes": "No marketing restrictions policy."},
        {"control_id": "PRV-011", "status": "Not Implemented", "notes": "No sale of PHI policy."},
        {"control_id": "PRV-012", "status": "Not Implemented", "notes": "No designated Privacy Officer."},
    ],
    "high_gaps": [
        {"control_id": "ADM-001", "status": "Partial", "notes": "Risk analysis 3 years stale."},
        {"control_id": "ADM-002", "status": "Partial", "notes": "Risk register has unmitigated items."},
        {"control_id": "ADM-015", "status": "Partial", "notes": "Missing ePHI specific breach notification."},
        {"control_id": "ADM-017", "status": "Partial", "notes": "DR plan never tested."},
        {"control_id": "ADM-018", "status": "Partial", "notes": "Emergency mode procedures not documented for ePHI."},
        {"control_id": "ADM-022", "status": "Partial", "notes": "BAAs missing for 3 sub-vendors with ePHI access."},
        {"control_id": "ADM-023", "status": "Not Implemented", "notes": "No annual HIPAA training program."},
        {"control_id": "ADM-019", "status": "Not Implemented", "notes": "DR plan never tested."},
        {"control_id": "BRN-001", "status": "Partial", "notes": "No four factor breach risk assessment template."},
        {"control_id": "BRN-005", "status": "Partial", "notes": "No internal BA to CE breach notification procedure or template."},
        {"control_id": "PHY-002", "status": "Partial", "notes": "No formal Facility Security Plan."},
        {"control_id": "PHY-004", "status": "Not Implemented", "notes": "No maintenance log for physical systems handling ePHI."},
        {"control_id": "PHY-009", "status": "Not Implemented", "notes": "No device or media movement tracking."},
        {"control_id": "PRV-013", "status": "Partial", "notes": "No Privacy Rule specific curriculum or retraining cadence."},
        {"control_id": "TEC-005", "status": "Partial", "notes": "Audit log retention only 90 days."},
        {"control_id": "TEC-006", "status": "Partial", "notes": "No formal integrity verification for ePHI exports."},
        {"control_id": "TEC-009", "status": "Partial", "notes": "Email TLS not confirmed for all routes."},
    ],
    "quick_wins": [
        {"control_id": "ADM-011", "status": "Partial", "notes": "Document monthly security reminder cadence."},
        {"control_id": "ADM-013", "status": "Partial", "notes": "Document Okta login monitoring procedure."},
        {"control_id": "PRV-012", "status": "Not Implemented", "notes": "Designate Privacy Officer; lightweight appointment doc."},
    ],
}
