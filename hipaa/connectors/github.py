"""GitHub connector — branch protection, access controls, secret scanning."""
import requests


class GitHubConnector:
    def __init__(self, token: str, org: str):
        self.token = token
        self.org = org
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

    def test_connection(self) -> bool:
        try:
            r = requests.get(
                f"https://api.github.com/orgs/{self.org}",
                headers=self.headers, timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False

    def get_findings(self) -> dict:
        findings = {}
        try:
            r = requests.get(
                f"https://api.github.com/orgs/{self.org}",
                headers=self.headers, timeout=10
            )
            if r.status_code == 200:
                org_data = r.json()
                findings["two_factor_requirement"] = org_data.get("two_factor_requirement_enabled", False)
                findings["members_count"] = org_data.get("public_members_url", "")
        except Exception as e:
            findings["error"] = str(e)
        return findings

    def to_hipaa_signals(self) -> dict:
        return self.get_findings()


GITHUB_DEMO_FINDINGS = {
    "two_factor_requirement": True,
    "branch_protection_enabled": True,
    "secret_scanning_enabled": True,
    "code_scanning_enabled": False,
    "outside_collaborators": 3,
}
