"""Slack connector — alerting output only."""
import requests


class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, message: str, blocks: list = None) -> bool:
        payload = {"text": message}
        if blocks:
            payload["blocks"] = blocks
        try:
            r = requests.post(self.webhook_url, json=payload, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def send_assessment_summary(self, org_name: str, score: float, critical_count: int) -> bool:
        color = "#DC2626" if score < 50 else ("#EAB308" if score < 75 else "#22C55E")
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"HIPAA Readiness Assessment — {org_name}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Overall Score:* {score:.1f}%"},
                    {"type": "mrkdwn", "text": f"*Critical Gaps:* {critical_count}"},
                ],
            },
        ]
        return self.send(f"HIPAA Assessment Complete — {org_name}: {score:.1f}%", blocks)
