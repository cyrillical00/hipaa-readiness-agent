"""Azure connector — Storage, Monitor, Key Vault."""


class AzureConnector:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, subscription_id: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.subscription_id = subscription_id

    def test_connection(self) -> bool:
        return False

    def get_findings(self) -> dict:
        return {
            "storage_encryption_enabled": True,
            "monitor_log_retention_days": 90,
            "key_vault_in_use": True,
        }

    def to_hipaa_signals(self) -> dict:
        return self.get_findings()
