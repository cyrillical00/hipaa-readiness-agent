"""Slack notification utilities for HIPAA assessment alerts."""
import streamlit as st
import os
from connectors.slack import SlackNotifier


def get_notifier() -> SlackNotifier | None:
    webhook = st.secrets.get("SLACK_WEBHOOK_URL", os.environ.get("SLACK_WEBHOOK_URL", ""))
    if not webhook:
        return None
    return SlackNotifier(webhook)


def notify_assessment_complete(org_name: str, score: float, critical_count: int) -> bool:
    notifier = get_notifier()
    if not notifier:
        return False
    return notifier.send_assessment_summary(org_name, score, critical_count)
