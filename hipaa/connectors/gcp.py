"""GCP connector — GCS, Cloud Audit Logs, CMEK."""


class GCPConnector:
    def __init__(self, service_account_json: str, project_id: str):
        self.service_account_json = service_account_json
        self.project_id = project_id

    def test_connection(self) -> bool:
        return False

    def get_findings(self) -> dict:
        return {
            "cmek_enabled": False,
            "cloud_audit_logs_enabled": True,
            "vpc_service_controls": False,
            "gcs_bucket_encryption": True,
        }

    def to_hipaa_signals(self) -> dict:
        return self.get_findings()


GCP_DEMO_FINDINGS = {
    "cmek_enabled": False,
    "cloud_audit_logs_enabled": True,
    "vpc_service_controls": False,
    "gcs_bucket_encryption": True,
}
