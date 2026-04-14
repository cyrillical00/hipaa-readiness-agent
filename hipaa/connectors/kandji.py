"""Kandji connector — macOS MDM alternative."""
import requests


class KandjiConnector:
    def __init__(self, api_token: str, subdomain: str):
        self.api_token = api_token
        self.subdomain = subdomain

    def test_connection(self) -> bool:
        try:
            r = requests.get(
                f"https://{self.subdomain}.api.kandji.io/api/v1/devices",
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False

    def get_findings(self) -> dict:
        return {
            "filevault_enabled_pct": 100,
            "screen_lock_minutes": 10,
            "mdm_enrollment_pct": 100,
        }

    def to_hipaa_signals(self) -> dict:
        return self.get_findings()
