"""Jira connector — incident tickets, remediation tracking."""
import requests
from requests.auth import HTTPBasicAuth


class JiraConnector:
    def __init__(self, url: str, email: str, api_token: str):
        self.url = url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json"}

    def test_connection(self) -> bool:
        try:
            r = requests.get(
                f"{self.url}/rest/api/3/myself",
                auth=self.auth, headers=self.headers, timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False

    def get_findings(self) -> dict:
        findings = {}
        try:
            r = requests.get(
                f"{self.url}/rest/api/3/search?jql=labels=HIPAA+AND+status!=Done&maxResults=50",
                auth=self.auth, headers=self.headers, timeout=10
            )
            if r.status_code == 200:
                issues = r.json().get("issues", [])
                findings["open_hipaa_tickets"] = len(issues)
                findings["overdue_tickets"] = len([
                    i for i in issues
                    if i.get("fields", {}).get("duedate") and
                    i["fields"]["duedate"] < "2024-01-01"
                ])
        except Exception as e:
            findings["error"] = str(e)
        return findings

    def to_hipaa_signals(self) -> dict:
        return self.get_findings()


JIRA_DEMO_FINDINGS = {
    "open_hipaa_tickets": 7,
    "overdue_tickets": 2,
    "incident_tickets_open": 1,
    "remediation_tickets_tracked": True,
}
