"""Outbound notifications for request-list reminders.

Pluggable by environment so the prototype runs with no mail server:
  - default: LogNotifier (writes the message to the audit log only)
  - SMTP_HOST set: SmtpNotifier sends email from SMTP_FROM
  - SMS_WEBHOOK_URL set: SmsNotifier POSTs {to, body} to that URL (Twilio via a Make/Zapier
    webhook, or any SMS gateway). SMS is only used when a list's channel is 'email+sms'.
"""
from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any

import httpx


@dataclass
class Delivery:
    channel: str            # email | sms | log
    to: str | None
    ok: bool
    detail: str = ""


class Notifier:
    def send_email(self, to: str | None, subject: str, body: str) -> Delivery:  # pragma: no cover - interface
        raise NotImplementedError

    def send_sms(self, to: str | None, body: str) -> Delivery:  # pragma: no cover - interface
        raise NotImplementedError


class LogNotifier(Notifier):
    """No transport configured: the reminder is drafted and recorded, a person sends it."""

    def __init__(self):
        self.sent: list[dict[str, Any]] = []

    def send_email(self, to, subject, body):
        self.sent.append({"channel": "email", "to": to, "subject": subject, "body": body})
        return Delivery("log", to, True, "no SMTP configured; reminder drafted only")

    def send_sms(self, to, body):
        self.sent.append({"channel": "sms", "to": to, "body": body})
        return Delivery("log", to, True, "no SMS gateway configured; reminder drafted only")


class SmtpNotifier(Notifier):
    def __init__(self):
        self.host = os.environ["SMTP_HOST"]
        self.port = int(os.environ.get("SMTP_PORT", "587"))
        self.user = os.environ.get("SMTP_USER")
        self.password = os.environ.get("SMTP_PASSWORD")
        self.sender = os.environ.get("SMTP_FROM", self.user or "noreply@example.com")
        self.sms = SmsNotifier() if os.environ.get("SMS_WEBHOOK_URL") else LogNotifier()

    def send_email(self, to, subject, body):
        if not to:
            return Delivery("email", None, False, "no client email on the request list")
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.sender, to, subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
                smtp.starttls()
                if self.user:
                    smtp.login(self.user, self.password or "")
                smtp.send_message(msg)
            return Delivery("email", to, True)
        except Exception as e:  # noqa: BLE001
            return Delivery("email", to, False, f"{type(e).__name__}: {e}")

    def send_sms(self, to, body):
        return self.sms.send_sms(to, body)


class SmsNotifier(Notifier):
    def __init__(self):
        self.url = os.environ["SMS_WEBHOOK_URL"]

    def send_email(self, to, subject, body):
        return Delivery("email", to, False, "SMS notifier cannot send email")

    def send_sms(self, to, body):
        if not to:
            return Delivery("sms", None, False, "no client phone on the request list")
        try:
            r = httpx.post(self.url, json={"to": to, "body": body}, timeout=30)
            r.raise_for_status()
            return Delivery("sms", to, True)
        except Exception as e:  # noqa: BLE001
            return Delivery("sms", to, False, f"{type(e).__name__}: {e}")


def build_notifier() -> Notifier:
    if os.environ.get("SMTP_HOST"):
        return SmtpNotifier()
    return LogNotifier()


def reminder_text(rl: dict, pending_items: list[dict], firm_name: str = "our office") -> tuple[str, str, str]:
    """(subject, email body, sms body) for a reminder on a request list."""
    first = (rl.get("client_name") or "there").split("&")[0].split(",")[0].strip()
    n = rl.get("reminder_number") or 1
    subject = f"Reminder: {len(pending_items)} item{'s' if len(pending_items) != 1 else ''} still needed for your {rl['tax_year']} return"
    lines = [f"Hi {first},", "", f"A quick reminder from {firm_name}. We are still waiting on the following for your {rl['tax_year']} return:", ""]
    lines += [f"  [ ] {it['item']}" for it in pending_items]
    lines += ["", "Please upload to the portal or reply to this email with attachments. If an item no longer applies, just tell us.",
              "", "Thank you,", firm_name]
    sms = f"{firm_name}: {len(pending_items)} item(s) still needed for your {rl['tax_year']} return, e.g. {pending_items[0]['item'][:60]}. Please upload or reply to our email. (reminder {n})"
    return subject, "\n".join(lines), sms
