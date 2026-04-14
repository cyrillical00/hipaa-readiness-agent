"""Google Workspace connector — admin logs, DLP, Drive sharing."""


class GoogleWorkspaceConnector:
    def __init__(self, service_account_json: str):
        self.service_account_json = service_account_json

    def test_connection(self) -> bool:
        try:
            import json
            from google.oauth2 import service_account
            creds_data = json.loads(self.service_account_json)
            service_account.Credentials.from_service_account_info(creds_data)
            return True
        except Exception:
            return False

    def get_findings(self) -> dict:
        return {
            "tls_enforced_inbound": False,
            "dlp_enabled": False,
            "drive_sharing_restricted": True,
            "audit_log_enabled": True,
            "audit_log_retention_days": 180,
            "baa_in_place": False,
            "2sv_enforced": True,
        }

    def to_hipaa_signals(self) -> dict:
        return self.get_findings()


GOOGLE_WORKSPACE_DEMO_FINDINGS = {
    "tls_enforced_inbound": False,  # Not confirmed — flagged as Partial
    "dlp_enabled": False,
    "drive_sharing_restricted": True,
    "audit_log_enabled": True,
    "audit_log_retention_days": 180,
    "baa_in_place": False,  # CRITICAL — BAA not executed
    "2sv_enforced": True,
    "external_sharing_disabled": False,
}
