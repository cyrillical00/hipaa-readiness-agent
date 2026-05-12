"""Demo persona definitions. Each persona is a self-contained dict with:
- key: short slug used by the selector
- name: display name
- summary: one paragraph callout shown when selected
- org_context: keys matching app.py session_state defaults (org_name, entity_type,
  ephi_systems, ephi_leaves_org, soc2_status, remote_workforce, workforce_size)
- control_statuses: dict of {control_id: {status, evidence, notes, alt_documented?}}
- baa_list: list of vendor dicts (matching DEMO_BAAS shape from data/sample_baas.py)
- assessment_results: precomputed scorer output (dict shape from engine.scorer.compute_readiness)
"""
from data.sample_baas import DEMO_BAAS


MERIDIAN_ORG_CONTEXT = {
    "org_name": "Meridian Health Tech",
    "entity_type": "Business Associate",
    "ephi_systems": ["Cloud Storage", "EHR Integration API", "Billing System", "Internal Messaging"],
    "ephi_leaves_org": True,
    "soc2_status": "Type I Complete",
    "remote_workforce": True,
    "workforce_size": 150,
}

MERIDIAN_CONTROL_STATUSES = {
    "ADM-001": {"status": "Partial", "evidence": True, "notes": "Risk analysis completed 3 years ago; not updated after cloud migration."},
    "ADM-002": {"status": "Partial", "evidence": True, "notes": "Risk register exists but several identified items are unmitigated."},
    "ADM-003": {"status": "Implemented", "evidence": True, "notes": "Sanction policy in employee handbook, last reviewed 8 months ago."},
    "ADM-004": {"status": "Partial", "evidence": False, "notes": "Logs exist in CloudTrail and Okta but no formal review procedure or cadence."},
    "ADM-005": {"status": "Implemented", "evidence": True, "notes": "VP of Engineering designated as Security Officer (informal, no formal appointment doc)."},
    "ADM-006": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Access authorization tied to Okta role assignments."},
    "ADM-007": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Background checks run on hire; periodic access reviews quarterly."},
    "ADM-008": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Offboarding checklist includes immediate Okta deprovisioning."},
    "ADM-009": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Access requests managed via Jira tickets with manager approval."},
    "ADM-010": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Quarterly access review process documented and executed."},
    "ADM-011": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Monthly Slack security reminders sent informally. No policy or tracking."},
    "ADM-012": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "CrowdStrike deployed on all managed endpoints."},
    "ADM-013": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Okta has login alerts but no formal monitoring procedure."},
    "ADM-014": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Password policy enforced via Okta: 12 char min, MFA required."},
    "ADM-015": {"status": "Partial", "evidence": True, "notes": "Incident response plan exists from SOC2 audit. No ePHI breach notification procedure."},
    "ADM-016": {"status": "Implemented", "evidence": True, "notes": "AWS S3 backups configured with daily snapshots."},
    "ADM-017": {"status": "Partial", "evidence": True, "notes": "DR plan documented but never tested in a tabletop exercise."},
    "ADM-018": {"status": "Partial", "evidence": False, "notes": "Emergency mode procedures not documented for ePHI systems specifically."},
    "ADM-019": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "DR plan has never been tested. No tabletop or failover exercise on record."},
    "ADM-020": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Systems classified in SOC2 scope but no ePHI-specific criticality matrix."},
    "ADM-021": {"status": "Not Implemented", "evidence": False, "notes": "No formal HIPAA evaluation performed since initial compliance review."},
    "ADM-022": {"status": "Partial", "evidence": False, "notes": "BAAs exist for primary hospital clients but 3 sub-vendors with ePHI access have no BAAs."},
    "ADM-023": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No documented annual HIPAA training program. Ad hoc onboarding mentions HIPAA briefly."},
    "PHY-001": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Cloud-primary org; primary facility has badge access. DR documented in BCP."},
    "PHY-002": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Office has physical security but no formal written Facility Security Plan."},
    "PHY-003": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Badge access exists; no documented role-based physical access matrix."},
    "PHY-004": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No formal maintenance log for physical systems in ePHI environment."},
    "PHY-005": {"status": "Implemented", "evidence": True, "notes": "Acceptable use policy covers workstations. Remote work addendum added last year."},
    "PHY-006": {"status": "Partial", "evidence": False, "notes": "Screen lock enforced on managed devices. 40% of remote workers use personal BYOD devices."},
    "PHY-007": {"status": "Implemented", "evidence": True, "notes": "Data disposal procedure documented; hardware vendor provides certificates of destruction."},
    "PHY-008": {"status": "Implemented", "evidence": True, "notes": "Media sanitization policy in place; NIST 800-88 referenced."},
    "PHY-009": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No formal device or media movement tracking. Jamf manages macOS fleet but no movement log."},
    "PHY-010": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "AWS backup procedures cover cloud storage. Physical media rarely moved."},
    "TEC-001": {"status": "Implemented", "evidence": True, "notes": "All users have unique Okta IDs. No shared accounts detected in last audit."},
    "TEC-002": {"status": "Implemented", "evidence": True, "notes": "Break-glass AWS account documented and tested annually."},
    "TEC-003": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "15-minute screen lock enforced via Okta and MDM."},
    "TEC-004": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "S3 SSE-AES256 enabled. RDS encrypted at rest with AWS KMS."},
    "TEC-005": {"status": "Partial", "evidence": True, "notes": "CloudTrail and Okta logs enabled. Retention set to 90 days (HIPAA guidance suggests 6 years)."},
    "TEC-006": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Database checksums enabled but no formal integrity verification process for ePHI exports."},
    "TEC-007": {"status": "Implemented", "evidence": True, "notes": "Okta MFA enforced for all users including contractors."},
    "TEC-008": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "TLS 1.2+ enforced on all API endpoints."},
    "TEC-009": {"status": "Partial", "evidence": False, "alt_documented": False, "notes": "APIs use TLS but internal email (Google Workspace) not confirmed for opportunistic TLS enforcement on all routes."},
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
    "BRN-001": {"status": "Partial", "evidence": False, "notes": "Incident response covers triage; no formal four factor breach risk assessment template or decision log."},
    "BRN-002": {"status": "Not Implemented", "evidence": False, "notes": "No individual notification template, content checklist, or delivery procedure."},
    "BRN-003": {"status": "Not Implemented", "evidence": False, "notes": "No media notification procedure. Threshold trigger (500+ residents per state) not flagged in incident playbook."},
    "BRN-004": {"status": "Not Implemented", "evidence": False, "notes": "No HHS submission procedure documented; no annual breach log maintained."},
    "BRN-005": {"status": "Partial", "evidence": False, "notes": "BAAs reference 60 day notification; no internal procedure, template, or affected individual identification workflow for BA to CE notice."},
    "BRN-006": {"status": "Not Implemented", "evidence": False, "notes": "No breach decision documentation log; no six year retention policy mapped to breach records."},
    "BRN-007": {"status": "Not Implemented", "evidence": False, "notes": "No standalone breach response plan. Relies on generic SOC2 incident plan with no breach specific roles, escalation, or notification ownership."},
}


BROOKLINE_ORG_CONTEXT = {
    "org_name": "Brookline Cardiology",
    "entity_type": "Covered Entity",
    "ephi_systems": ["EHR", "Email", "Billing System"],
    "ephi_leaves_org": False,
    "soc2_status": "None",
    "remote_workforce": False,
    "workforce_size": 25,
}

BROOKLINE_CONTROL_STATUSES = {
    "ADM-001": {"status": "Not Implemented", "evidence": False, "notes": "No formal risk analysis on file. Office manager reviews insurance forms annually but no documented ePHI risk assessment."},
    "ADM-002": {"status": "Not Implemented", "evidence": False, "notes": "No risk management program. Issues addressed reactively by IT contractor when reported."},
    "ADM-003": {"status": "Partial", "evidence": True, "notes": "Sanction language in the employee handbook signed at hire; no formal escalation or tracking when violations occur."},
    "ADM-004": {"status": "Not Implemented", "evidence": False, "notes": "EHR has audit logs available but no one reviews them. No procedure or review cadence."},
    "ADM-005": {"status": "Partial", "evidence": False, "notes": "Practice manager designated as Security Officer informally; no written appointment, no documented duties."},
    "ADM-006": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "EHR roles tied to job function; office manager approves EHR account creation."},
    "ADM-007": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Background checks done at hire through third party. Periodic access reviews not performed."},
    "ADM-008": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Termination checklist disables EHR account same day; key card collected."},
    "ADM-009": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Account creation handled informally by EHR vendor support; no ticketing or written approval trail."},
    "ADM-010": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No periodic access review process. Last EHR account audit was at the EHR upgrade two years ago."},
    "ADM-011": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Annual HIPAA refresher delivered at staff meeting; no awareness reminders or phishing simulations between sessions."},
    "ADM-012": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Windows Defender on workstations. No central EDR or alerting; IT contractor reviews on visit."},
    "ADM-013": {"status": "Not Implemented", "evidence": False, "alt_documented": None, "notes": "No login monitoring beyond EHR vendor's standard reporting. No alerts on failed logins."},
    "ADM-014": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "EHR enforces 10 character password and 90 day rotation. MFA required for remote EHR access."},
    "ADM-015": {"status": "Partial", "evidence": False, "notes": "IT contractor handles incidents ad hoc. No written incident response plan or notification chain."},
    "ADM-016": {"status": "Implemented", "evidence": True, "notes": "EHR vendor manages encrypted backups; cloud backup service runs nightly for billing data."},
    "ADM-017": {"status": "Partial", "evidence": False, "notes": "EHR vendor advertises 4 hour RTO; practice has not validated or documented its own DR steps."},
    "ADM-018": {"status": "Not Implemented", "evidence": False, "notes": "No emergency mode operations procedure. Paper charting fallback is informal practice, not documented."},
    "ADM-019": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "No DR test on record. Vendor performs its own; practice has never validated."},
    "ADM-020": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Staff knows EHR is the critical system; no written application criticality analysis."},
    "ADM-021": {"status": "Not Implemented", "evidence": False, "notes": "No periodic technical or non-technical evaluation. Last review was during initial EHR install."},
    "ADM-022": {"status": "Partial", "evidence": False, "notes": "BAA on file for EHR vendor and cloud backup; missing for IT contractor and billing service. See BAA tracker."},
    "ADM-023": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Annual HIPAA training delivered verbally at staff meeting using vendor-provided slides; attendance not consistently tracked, no role-based modules."},
    "PHY-001": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Single office; alarm system, badge entry to clinical area, after-hours monitoring."},
    "PHY-002": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Written Facility Security Plan covering building access, server room, and visitor policy."},
    "PHY-003": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Badge access matrix kept by office manager. Server room limited to office manager and IT contractor."},
    "PHY-004": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "IT contractor logs visits informally; no written maintenance log for the server room."},
    "PHY-005": {"status": "Implemented", "evidence": True, "notes": "Workstations live in clinical rooms; staff are trained to log out before leaving the room."},
    "PHY-006": {"status": "Implemented", "evidence": True, "notes": "Screen privacy filters deployed; auto-lock enforced at 5 minutes; no BYOD allowed."},
    "PHY-007": {"status": "Implemented", "evidence": True, "notes": "Shred bins onsite emptied weekly by certified vendor; certificates retained."},
    "PHY-008": {"status": "Implemented", "evidence": True, "notes": "Old hard drives degaussed by IT contractor; certificates of sanitization kept on file."},
    "PHY-009": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Workstation moves logged informally; no written movement record for portable devices."},
    "PHY-010": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Backup tapes rotated weekly to fireproof safe; cloud backup verified monthly."},
    "TEC-001": {"status": "Implemented", "evidence": True, "notes": "Every staff member has a unique EHR login. Shared credentials prohibited and audited yearly."},
    "TEC-002": {"status": "Partial", "evidence": False, "notes": "EHR vendor has emergency access via support; practice does not have its own break-glass account documented."},
    "TEC-003": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "Workstations lock at 15 minutes; reception terminals exempted by request. No documented exception policy."},
    "TEC-004": {"status": "Not Implemented", "evidence": False, "alt_documented": False, "notes": "EHR database encrypted at rest by vendor; local file shares used by billing staff and shared workstation drives are not encrypted at rest."},
    "TEC-005": {"status": "Partial", "evidence": False, "notes": "EHR captures user activity but logs are kept only 30 days and never reviewed by the practice."},
    "TEC-006": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "EHR vendor handles internal integrity checks; no documented procedure for exports or local files."},
    "TEC-007": {"status": "Not Implemented", "evidence": False, "notes": "No central audit log review. Each system has its own log; no aggregation or alerts."},
    "TEC-008": {"status": "Partial", "evidence": False, "alt_documented": None, "notes": "EHR vendor handles its own integrity in transit. Practice has no documented stance on email or fax integrity."},
    "TEC-009": {"status": "Partial", "evidence": False, "alt_documented": False, "notes": "Outbound email is TLS-opportunistic; no enforced TLS for clinical referral messages."},
    "PRV-001": {"status": "Implemented", "evidence": True, "notes": "Notice of Privacy Practices posted in waiting room and on the practice website. Acknowledgment captured at intake."},
    "PRV-002": {"status": "Implemented", "evidence": True, "notes": "Patients can request records via written form; office manager fulfills within 30 days. Log maintained."},
    "PRV-003": {"status": "Implemented", "evidence": True, "notes": "Amendment request form available; physician reviews and approves or denies in writing within 60 days."},
    "PRV-004": {"status": "Partial", "evidence": False, "notes": "Disclosure log kept for subpoena and law enforcement disclosures; routine TPO disclosures not separately logged."},
    "PRV-005": {"status": "Implemented", "evidence": True, "notes": "Patients can request restrictions in writing; practice evaluates and responds. Self-pay restriction policy documented."},
    "PRV-006": {"status": "Implemented", "evidence": True, "notes": "Confidential communication requests honored; alternative phone and address fields used in EHR."},
    "PRV-007": {"status": "Implemented", "evidence": True, "notes": "Minimum necessary policy in employee handbook; role-based EHR access enforces it for clinical and billing roles."},
    "PRV-008": {"status": "Implemented", "evidence": True, "notes": "Authorization form used for any non-TPO disclosure. Forms retained six years."},
    "PRV-009": {"status": "Partial", "evidence": False, "notes": "Verbal verification used for personal representatives; no written documentation procedure."},
    "PRV-010": {"status": "Implemented", "evidence": True, "notes": "Practice does not market patient services. Policy in handbook prohibits marketing use of PHI without authorization."},
    "PRV-011": {"status": "Implemented", "evidence": True, "notes": "Sale of PHI prohibited in written policy. No revenue arrangements involve PHI."},
    "PRV-012": {"status": "Implemented", "evidence": True, "notes": "Office manager designated as Privacy Officer in writing. Contact information posted with the Notice of Privacy Practices."},
    "PRV-013": {"status": "Implemented", "evidence": True, "notes": "Annual Privacy Rule training delivered alongside Security Rule training. Attendance tracked."},
    "BRN-001": {"status": "Partial", "evidence": False, "notes": "Office manager triages incidents informally; no four factor breach risk assessment template or decision documentation."},
    "BRN-002": {"status": "Partial", "evidence": False, "notes": "Practice has notified affected individuals once previously by letter; no reusable template, content checklist, or written procedure."},
    "BRN-003": {"status": "Not Implemented", "evidence": False, "notes": "No media notification procedure. 500+ resident threshold not flagged anywhere in the practice's playbook."},
    "BRN-004": {"status": "Not Implemented", "evidence": False, "notes": "No HHS Secretary submission procedure. Office manager unaware of annual breach log requirement."},
    "BRN-005": {"status": "N/A (Documented)", "evidence": True, "notes": "BA to CE notification not applicable; Brookline is the Covered Entity. Documented in scope statement."},
    "BRN-006": {"status": "Partial", "evidence": False, "notes": "Past breach correspondence retained in office manager's email; no formal breach documentation log or six year retention policy."},
    "BRN-007": {"status": "Partial", "evidence": False, "notes": "Office manager has notes on prior incident handling; no standalone breach response plan with roles, timelines, and notification ownership."},
}

BROOKLINE_BAAS = [
    {
        "vendor": "Epic SmartCare Lite (EHR vendor)",
        "services": "On-premises EHR with vendor-managed backup",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2021-04-01",
        "baa_review_date": "2025-04-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "Primary EHR vendor. BAA executed with original install. Sub-processors disclosed annually.",
    },
    {
        "vendor": "Atlantic Medical Billing",
        "services": "Outsourced medical billing and claims processing",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2020-09-01",
        "baa_review_date": "2023-09-01",
        "sub_bas_disclosed": False,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "HIGH: BAA expired September 2023. Billing service still actively handling claims with full ePHI access. Renewal not initiated.",
    },
    {
        "vendor": "Brookline IT Services (contractor)",
        "services": "On-site IT support, server room access, workstation management",
        "ephi_shared": True,
        "baa_in_place": False,
        "baa_signed_date": None,
        "baa_review_date": None,
        "sub_bas_disclosed": False,
        "security_incident_clause": False,
        "breach_notification_window": "not specified",
        "notes": "CRITICAL: IT contractor has physical and admin access to EHR server. No BAA executed; verbal agreement only.",
    },
    {
        "vendor": "Carbonite Cloud Backup",
        "services": "Encrypted offsite backup of billing files",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2022-06-15",
        "baa_review_date": "2025-06-15",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "Cloud backup vendor. BAA executed; backup encryption verified.",
    },
]


NORTHEAST_ORG_CONTEXT = {
    "org_name": "Northeast Health Network",
    "entity_type": "Both",
    "ephi_systems": ["EHR", "EHR Integration API", "Patient Portal", "Billing System", "Cloud Storage", "Email"],
    "ephi_leaves_org": True,
    "soc2_status": "Type II Complete",
    "remote_workforce": True,
    "workforce_size": 800,
}

NORTHEAST_CONTROL_STATUSES = {
    "ADM-001": {"status": "Implemented", "evidence": True, "notes": "Enterprise risk analysis refreshed annually by internal GRC team; last refresh 4 months ago covers EHR, integration, and patient portal."},
    "ADM-002": {"status": "Implemented", "evidence": True, "notes": "Risk register tracked in Archer; remediation owners and target dates assigned."},
    "ADM-003": {"status": "Implemented", "evidence": True, "notes": "Sanction policy reviewed annually by HR and Compliance; documented enforcement history."},
    "ADM-004": {"status": "Implemented", "evidence": True, "notes": "Splunk-based SIEM ingests EHR, Okta, AWS, and patient portal logs; daily and weekly review procedures documented."},
    "ADM-005": {"status": "Partial", "evidence": True, "notes": "CISO formally appointed by board resolution; technology arm Security Officer designation is still in transition after the reorg, so escalations sometimes route through the wrong leader."},
    "ADM-006": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Access authorization workflow in ServiceNow with role-owner and data-owner approvals."},
    "ADM-007": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Background checks managed by HR vendor; reverification on role change."},
    "ADM-008": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Joiner-mover-leaver automated through HRIS to Okta with same-day deprovisioning SLA."},
    "ADM-009": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Access requests handled via ServiceNow with manager and data-owner approvals; full audit trail."},
    "ADM-010": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Quarterly access reviews automated through Lumos; certifications captured for SOC2."},
    "ADM-011": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "KnowBe4 monthly phishing simulations and quarterly security awareness modules; metrics reported to CISO."},
    "ADM-012": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "CrowdStrike Falcon deployed enterprise-wide with managed detection and response."},
    "ADM-013": {"status": "Partial", "evidence": True, "alt_documented": None, "notes": "SIEM correlation rules for failed logins and impossible travel run 24x7; tuning has not caught up to the new patient portal stand-up, so portal alerts route to the wrong on-call queue."},
    "ADM-014": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Okta-enforced password policy (14 character min, FIDO2 for privileged users, MFA for all)."},
    "ADM-015": {"status": "Implemented", "evidence": True, "notes": "Incident response plan reviewed annually; tabletop completed last quarter; ePHI breach playbook integrated."},
    "ADM-016": {"status": "Implemented", "evidence": True, "notes": "Encrypted backups with cross-region replication; recovery SLAs measured monthly."},
    "ADM-017": {"status": "Implemented", "evidence": True, "notes": "DR plan tested twice annually with full failover exercise; results reviewed by executive committee."},
    "ADM-018": {"status": "Partial", "evidence": True, "notes": "Emergency mode operations documented for the EHR. Patient portal and integration platform downtime procedures have not been refreshed since last year's reorg."},
    "ADM-019": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Two annual DR tests with full executive review; remediation actions tracked through closure."},
    "ADM-020": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Application criticality matrix maintained; all ePHI systems classified as Tier 1."},
    "ADM-021": {"status": "Partial", "evidence": True, "notes": "Annual HIPAA evaluation completed by internal audit last year; current cycle is in progress and behind schedule due to the reorg."},
    "ADM-022": {"status": "Partial", "evidence": True, "notes": "Vendor management program tracks BAAs and gates new vendors through procurement; recent clinical research partnership executed a data use agreement before the BAA cleared procurement, leaving one active gap."},
    "ADM-023": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Annual HIPAA training assigned in LMS to every workforce member; completion enforced; role-based modules."},
    "PHY-001": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Multiple data centers with biometric controls; managed by enterprise facilities team; reviewed in SOC2."},
    "PHY-002": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Facility Security Plan published and reviewed annually; covers all hospital and corporate sites."},
    "PHY-003": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Role-based physical access matrix maintained by facilities; quarterly review with managers."},
    "PHY-004": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "CMMS-tracked maintenance log for data center and clinical systems; vendor visits logged."},
    "PHY-005": {"status": "Implemented", "evidence": True, "notes": "Workstation use policy in handbook; remote work addendum and BYOD policy enforced through MDM."},
    "PHY-006": {"status": "Implemented", "evidence": True, "notes": "Privacy filters required at clinical workstations; remote workforce uses managed devices only via Intune and Jamf."},
    "PHY-007": {"status": "Implemented", "evidence": True, "notes": "Centralized media disposal program; vendor-issued certificates of destruction archived for six years."},
    "PHY-008": {"status": "Implemented", "evidence": True, "notes": "Media sanitization aligned with NIST 800-88; verified disposal for retired storage arrays."},
    "PHY-009": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Asset tracking system records device movement; loaner workstations checked out via ITSM."},
    "PHY-010": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Backup media handling procedures documented; cross-region cloud replication verified quarterly."},
    "TEC-001": {"status": "Implemented", "evidence": True, "notes": "Unique enterprise IDs from HRIS provisioned to all systems; no shared accounts; service accounts vaulted."},
    "TEC-002": {"status": "Implemented", "evidence": True, "notes": "Break-glass procedures for EHR and cloud documented; tested annually; access alerts reviewed by SOC."},
    "TEC-003": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "10 minute idle lock enforced via Intune and Jamf for all managed endpoints."},
    "TEC-004": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "Encryption at rest enforced across EHR storage, integration buses, S3 buckets, and laptops via FileVault and BitLocker."},
    "TEC-005": {"status": "Partial", "evidence": True, "notes": "SIEM retention configured to seven years for core ePHI systems; patient portal logs only retained 90 days due to a configuration drift caught last month."},
    "TEC-006": {"status": "Partial", "evidence": True, "alt_documented": None, "notes": "Integrity controls verified on integration jobs through hashing; reconciliation reports reviewed weekly for the EHR feed; partner-feed integrity reviews are quarterly only."},
    "TEC-007": {"status": "Partial", "evidence": True, "notes": "Centralized log review program runs daily for clinical systems; weekly review of patient portal and integration logs has slipped twice this quarter due to staffing turnover."},
    "TEC-008": {"status": "Implemented", "evidence": True, "alt_documented": None, "notes": "TLS 1.2+ enforced on all external endpoints; mTLS for integration partners; quarterly cipher review."},
    "TEC-009": {"status": "Partial", "evidence": True, "alt_documented": None, "notes": "Mandatory TLS for outbound clinical email via Mimecast; one legacy fax-to-email gateway still falls back to opportunistic TLS pending decommission."},
    "PRV-001": {"status": "Implemented", "evidence": True, "notes": "Notice of Privacy Practices published on patient portal and posted at every facility; acknowledgment tracked."},
    "PRV-002": {"status": "Implemented", "evidence": True, "notes": "Patient access request workflow in HIM; fulfillment SLA tracked monthly; portal self-service enabled."},
    "PRV-003": {"status": "Implemented", "evidence": True, "notes": "Amendment requests processed by HIM with physician review; written response within 60 days."},
    "PRV-004": {"status": "Implemented", "evidence": True, "notes": "Disclosure accounting captured in EHR for all non-TPO disclosures; report available on demand."},
    "PRV-005": {"status": "Implemented", "evidence": True, "notes": "Restriction request workflow documented; self-pay restriction honored at registration."},
    "PRV-006": {"status": "Implemented", "evidence": True, "notes": "Confidential communications honored across email, phone, and mail channels; documented in patient profile."},
    "PRV-007": {"status": "Implemented", "evidence": True, "notes": "Minimum necessary enforced through role-based access in EHR; audited via Splunk; exceptions reviewed."},
    "PRV-008": {"status": "Implemented", "evidence": True, "notes": "Authorization workflow integrated with HIM and research office; all non-TPO disclosures documented."},
    "PRV-009": {"status": "Partial", "evidence": True, "notes": "Personal representative verification workflow standardized at registration; pediatric and adult guardianship edge cases handled inconsistently across regions."},
    "PRV-010": {"status": "Implemented", "evidence": True, "notes": "Marketing policy reviewed by Compliance; marketing communications go through Privacy Office for authorization review."},
    "PRV-011": {"status": "Implemented", "evidence": True, "notes": "Sale of PHI prohibited; revenue arrangements reviewed by General Counsel and Privacy Office."},
    "PRV-012": {"status": "Implemented", "evidence": True, "notes": "Chief Privacy Officer formally appointed; dedicated Privacy Office with regional leads."},
    "PRV-013": {"status": "Partial", "evidence": True, "notes": "Annual Privacy Rule training delivered in LMS for clinical and registration staff; technology arm engineers were missed in the first cycle after the reorg moved them under a different leader."},
    "BRN-001": {"status": "Partial", "evidence": True, "notes": "Four factor breach risk assessment template embedded in incident workflow; reorg moved the decision approver out of the playbook, leaving sign-off ambiguous on borderline cases."},
    "BRN-002": {"status": "Partial", "evidence": False, "notes": "Individual notification template exists; recent reorg moved Privacy Office and Compliance under different leaders, leaving notification approver chain unclear in the playbook."},
    "BRN-003": {"status": "Partial", "evidence": False, "notes": "Media notification procedure documented but reorg has not refreshed the on-call media spokesperson and 500+ resident threshold escalation owner."},
    "BRN-004": {"status": "Partial", "evidence": True, "notes": "Annual HHS breach log maintained by Privacy Office; current year's submission ownership unsettled because the reorg moved the responsible director."},
    "BRN-005": {"status": "Partial", "evidence": True, "notes": "BA to CE notification procedure documented for the technology arm; the affected-individual identification workflow has not been re-tested since the integration platform changed leaders."},
    "BRN-006": {"status": "Implemented", "evidence": True, "notes": "Breach decisions logged in GRC platform; six year retention policy applied; immutable archive."},
    "BRN-007": {"status": "Partial", "evidence": True, "notes": "Standalone breach response plan exists with named roles and an escalation tree; reorg has not refreshed the on-call notification owner or executive sponsor for the technology arm."},
}

NORTHEAST_BAAS = [
    {
        "vendor": "Epic Systems",
        "services": "Enterprise EHR, MyChart patient portal",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2018-05-01",
        "baa_review_date": "2025-05-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "30 days",
        "notes": "Primary EHR vendor. Enterprise BAA covers all subsidiaries.",
    },
    {
        "vendor": "Microsoft Azure",
        "services": "Cloud infrastructure, integration services, Office 365",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2020-01-15",
        "baa_review_date": "2025-01-15",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "30 days",
        "notes": "Tenant-wide BAA executed; HIPAA-eligible services scoped in shared responsibility matrix.",
    },
    {
        "vendor": "Amazon Web Services",
        "services": "Data lake, integration platform, S3 archive",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2019-08-01",
        "baa_review_date": "2025-08-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "BAA covers HIPAA-eligible services. Reviewed annually by GRC.",
    },
    {
        "vendor": "Salesforce Health Cloud",
        "services": "Population health and outreach",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2022-04-01",
        "baa_review_date": "2025-04-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "30 days",
        "notes": "Health Cloud edition; BAA executed at procurement.",
    },
    {
        "vendor": "Mimecast",
        "services": "Email security and TLS enforcement",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2021-03-01",
        "baa_review_date": "2025-03-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "30 days",
        "notes": "Filtering and TLS enforcement for clinical email; BAA in place.",
    },
    {
        "vendor": "Splunk Cloud",
        "services": "SIEM and log analytics",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2021-06-01",
        "baa_review_date": "2025-06-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "Log streams may contain ePHI; BAA executed and reviewed annually.",
    },
    {
        "vendor": "ServiceNow",
        "services": "ITSM, incident management, access requests",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2020-11-01",
        "baa_review_date": "2025-11-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "Tickets may reference ePHI in incident records; BAA in place.",
    },
    {
        "vendor": "Okta",
        "services": "Identity and access management",
        "ephi_shared": False,
        "baa_in_place": True,
        "baa_signed_date": "2021-09-01",
        "baa_review_date": "2026-01-30",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "48h",
        "notes": "Identity-only data; BAA maintained as precaution. Renewal scheduled within 90 days.",
    },
    {
        "vendor": "Workday",
        "services": "HRIS and joiner-mover-leaver source of truth",
        "ephi_shared": False,
        "baa_in_place": False,
        "baa_signed_date": None,
        "baa_review_date": None,
        "sub_bas_disclosed": False,
        "security_incident_clause": False,
        "breach_notification_window": "not specified",
        "notes": "HR system only; no ePHI processed. BAA not required per data flow review.",
    },
    {
        "vendor": "CrowdStrike",
        "services": "EDR and managed detection",
        "ephi_shared": False,
        "baa_in_place": True,
        "baa_signed_date": "2022-01-01",
        "baa_review_date": "2026-01-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "24h",
        "notes": "Telemetry only; BAA executed as precaution.",
    },
    {
        "vendor": "Iron Mountain",
        "services": "Records storage and shredding",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2017-10-01",
        "baa_review_date": "2025-10-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "Paper record storage and destruction; certificates retained.",
    },
    {
        "vendor": "Twilio",
        "services": "Patient SMS reminders and notifications",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2022-07-01",
        "baa_review_date": "2025-07-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "Appointment reminders only; BAA executed for HIPAA-eligible messaging.",
    },
    {
        "vendor": "Zoom for Healthcare",
        "services": "Telehealth video visits",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2020-04-01",
        "baa_review_date": "2025-04-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "Telehealth platform; BAA in place; encrypted recordings.",
    },
    {
        "vendor": "InterSystems HealthShare",
        "services": "Health information exchange",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2019-12-01",
        "baa_review_date": "2025-12-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "30 days",
        "notes": "HIE integration; BAA executed at onboarding.",
    },
    {
        "vendor": "Optum Pharmacy Services",
        "services": "Pharmacy benefit management",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2021-02-01",
        "baa_review_date": "2026-02-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "30 days",
        "notes": "PBM partner; BAA renewed in 2025.",
    },
    {
        "vendor": "Cardinal Health",
        "services": "Pharmacy distribution and inventory",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2020-06-01",
        "baa_review_date": "2026-03-15",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "Distribution partner; minimal ePHI exposure tied to medication histories.",
    },
    {
        "vendor": "Northeast Clinical Research Partners",
        "services": "Clinical trial coordination",
        "ephi_shared": True,
        "baa_in_place": False,
        "baa_signed_date": None,
        "baa_review_date": None,
        "sub_bas_disclosed": False,
        "security_incident_clause": False,
        "breach_notification_window": "not specified",
        "notes": "HIGH: Recent partnership; data use agreement signed but BAA still pending procurement review.",
    },
    {
        "vendor": "Press Ganey",
        "services": "Patient experience surveys",
        "ephi_shared": True,
        "baa_in_place": True,
        "baa_signed_date": "2022-09-01",
        "baa_review_date": "2025-09-01",
        "sub_bas_disclosed": True,
        "security_incident_clause": True,
        "breach_notification_window": "60 days",
        "notes": "Survey vendor; BAA in place; minimum necessary fields shared.",
    },
]


_MERIDIAN_SUMMARY = (
    "Meridian Health Tech is a 150-person SaaS Business Associate that runs EHR integration "
    "middleware for three hospital clients. SOC2 Type I closed 14 months ago, but no one has "
    "looked at the BAA portfolio in two years. Five vendors with active ePHI access have "
    "missing or expired BAAs, and Privacy plus Breach Notification programs barely exist "
    "because the org assumed the Covered Entities owned all of it. Score lands in the Partial "
    "band. Start at the Roadmap to see how the BAA gaps cascade into Phase 1 priority work."
)

_BROOKLINE_SUMMARY = (
    "Brookline Cardiology is a 25-person specialty practice acting as a Covered Entity. "
    "On-premises EHR, single office, almost no cloud. Privacy Rule maturity is strong because "
    "patient-facing obligations have always been front of mind, and physical safeguards are "
    "in good shape. The Security Rule is the soft spot: no risk analysis, no audit log review, "
    "no formal IT trust. ePHI does not meaningfully leave the org. Start at the Gap Assessment "
    "to see how Privacy carries the score while Administrative and Technical controls drag it down."
)

_NORTHEAST_SUMMARY = (
    "Northeast Health Network is an 800-person hospital and technology arm that operates as "
    "both a Covered Entity and a Business Associate. SOC2 Type II is complete, the GRC program "
    "is mature, and most controls are Implemented with evidence. A recent reorganization split "
    "Privacy and Compliance under different leaders, leaving the individual and media breach "
    "notification approver chain ambiguous. Score lands in the Mostly Ready band. Start at "
    "Breach Notification to see exactly how a small org change creates targeted residual risk."
)


def _build_meridian_assessment():
    return _compute_persona_results(MERIDIAN_CONTROL_STATUSES, MERIDIAN_ORG_CONTEXT)


def _build_brookline_assessment():
    return _compute_persona_results(BROOKLINE_CONTROL_STATUSES, BROOKLINE_ORG_CONTEXT)


def _build_northeast_assessment():
    return _compute_persona_results(NORTHEAST_CONTROL_STATUSES, NORTHEAST_ORG_CONTEXT)


def _compute_persona_results(statuses, context):
    import json
    import os
    from engine.scorer import compute_readiness

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    controls_path = os.path.join(here, "hipaa_controls.json")
    with open(controls_path, "r", encoding="utf-8") as fh:
        controls = json.load(fh)
    result = compute_readiness(controls, statuses, context)
    result["overall"] = round(result["overall"], 1)
    return result


PERSONAS = {
    "meridian": {
        "key": "meridian",
        "name": "Meridian Health Tech (BA, SaaS)",
        "summary": _MERIDIAN_SUMMARY,
        "org_context": MERIDIAN_ORG_CONTEXT,
        "control_statuses": MERIDIAN_CONTROL_STATUSES,
        "baa_list": list(DEMO_BAAS),
        "assessment_results": None,
    },
    "brookline": {
        "key": "brookline",
        "name": "Brookline Cardiology (CE, small practice)",
        "summary": _BROOKLINE_SUMMARY,
        "org_context": BROOKLINE_ORG_CONTEXT,
        "control_statuses": BROOKLINE_CONTROL_STATUSES,
        "baa_list": BROOKLINE_BAAS,
        "assessment_results": None,
    },
    "northeast": {
        "key": "northeast",
        "name": "Northeast Health Network (Both, mature)",
        "summary": _NORTHEAST_SUMMARY,
        "org_context": NORTHEAST_ORG_CONTEXT,
        "control_statuses": NORTHEAST_CONTROL_STATUSES,
        "baa_list": NORTHEAST_BAAS,
        "assessment_results": None,
    },
}


def _ensure_assessment(key):
    persona = PERSONAS[key]
    if persona["assessment_results"] is None:
        persona["assessment_results"] = _compute_persona_results(
            persona["control_statuses"], persona["org_context"]
        )
    return persona


def get_persona(key):
    if key not in PERSONAS:
        return None
    return _ensure_assessment(key)


def list_personas():
    out = []
    for key in PERSONAS:
        persona = _ensure_assessment(key)
        out.append({
            "key": persona["key"],
            "name": persona["name"],
            "summary": persona["summary"],
            "ephi_leaves_org": persona["org_context"].get("ephi_leaves_org"),
            "entity_type": persona["org_context"].get("entity_type"),
            "workforce_size": persona["org_context"].get("workforce_size"),
            "soc2_status": persona["org_context"].get("soc2_status"),
            "overall": persona["assessment_results"]["overall"],
            "band_label": persona["assessment_results"]["band_label"],
        })
    return out
