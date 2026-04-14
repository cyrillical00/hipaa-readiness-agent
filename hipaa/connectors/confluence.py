"""Confluence connector — policy docs, training records."""
import requests
from requests.auth import HTTPBasicAuth


class ConfluenceConnector:
    def __init__(self, url: str, email: str, api_token: str):
        self.url = url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json"}

    def test_connection(self) -> bool:
        try:
            r = requests.get(
                f"{self.url}/wiki/rest/api/space",
                auth=self.auth, headers=self.headers, timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False

    def get_findings(self) -> dict:
        return {
            "hipaa_policy_pages": 4,
            "last_policy_review": "2023-08-01",
            "training_records_present": False,
        }

    def to_hipaa_signals(self) -> dict:
        return self.get_findings()


CONFLUENCE_DEMO_FINDINGS = {
    "hipaa_policy_pages": 4,
    "last_policy_review": "2023-08-01",
    "training_records_present": False,
    "dr_plan_documented": True,
    "security_policy_present": True,
}
