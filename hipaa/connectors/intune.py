"""Microsoft Intune connector — Windows device posture."""


class IntuneConnector:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret

    def test_connection(self) -> bool:
        return False  # Requires Azure AD app registration

    def get_findings(self) -> dict:
        return {
            "bitlocker_enabled_pct": 95,
            "compliance_policy_pct": 90,
            "remote_wipe_capable": True,
            "managed_device_count": 45,
        }

    def to_hipaa_signals(self) -> dict:
        return self.get_findings()


INTUNE_DEMO_FINDINGS = {
    "bitlocker_enabled_pct": 95,
    "compliance_policy_pct": 90,
    "remote_wipe_capable": True,
    "managed_device_count": 45,
}
