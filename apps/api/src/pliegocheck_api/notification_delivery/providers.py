"""Proveedores SMTP y webhook firmado; no conocen ORM ni transacciones."""
# mypy: disable-error-code="type-arg"

import hmac
import ipaddress
import json
import smtplib
import socket
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import parseaddr
from hashlib import sha256
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from pliegocheck_api.config import Settings

TEMPLATE_DIR = Path(__file__).parents[5] / "config" / "notification-templates" / "v1"


@dataclass(frozen=True)
class ProviderResult:
    delivered: bool
    retryable: bool = False
    status_code: int | None = None
    provider_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    retry_after: int | None = None


def validate_email(address: str, allowed_domains: list[str]) -> str:
    if "\r" in address or "\n" in address:
        raise ValueError("EMAIL_HEADER_INJECTION")
    display, parsed = parseaddr(address.strip().lower())
    if display or parsed != address.strip().lower() or parsed.count("@") != 1:
        raise ValueError("EMAIL_INVALID")
    local, domain = parsed.rsplit("@", 1)
    if not local or "." not in domain or (allowed_domains and domain not in allowed_domains):
        raise ValueError("EMAIL_DOMAIN_NOT_ALLOWED")
    return parsed


def _safe_link(value: object) -> str:
    text = str(value or "")
    parsed = urlsplit(text)
    if text.startswith("/") or (parsed.scheme in {"http", "https"} and parsed.hostname):
        return text
    return "#"


def render_email(payload: dict, delivery_id: str) -> tuple[str, str, str]:
    opportunity = payload.get("opportunity") or {}
    alert = payload.get("alert") or {}
    monitor = payload.get("monitor") or {}
    links = payload.get("links") or {}
    opportunity_link = _safe_link(links.get("opportunity") or payload.get("opportunity_link", ""))
    secop_link = _safe_link(links.get("secop"))
    values = {
        "title": str(payload.get("title", "Alerta PliegoCheck")),
        "severity": str(payload.get("severity", "INFO")),
        "alert_type": str(alert.get("type") or payload.get("event_type", "ALERT")),
        "summary": str(payload.get("summary", "")),
        "entity_name": str(opportunity.get("entity_name") or "No disponible"),
        "process_title": str(opportunity.get("title") or "No disponible"),
        "outcome": str(opportunity.get("outcome") or "UNKNOWN"),
        "compatibility_score": str(opportunity.get("compatibility_score") or "UNKNOWN"),
        "urgency_status": str(opportunity.get("urgency_status") or "UNKNOWN"),
        "closing_date": str(opportunity.get("closing_date") or "No disponible"),
        "reason_code": str(alert.get("reason_code") or "No disponible"),
        "monitor_name": str(monitor.get("name") or "No disponible"),
        "opportunity_link": opportunity_link,
        "secop_link": secop_link if secop_link != "#" else "No disponible",
        "secop_href": secop_link,
        "disclaimer": str(payload["disclaimer"]),
        "delivery_id": delivery_id,
    }
    prefix = "digest" if payload.get("event_type") == "NOTIFICATION_DIGEST" else "alert"
    subject_template = (TEMPLATE_DIR / f"{prefix}-email-subject.txt").read_text(encoding="utf-8")
    text_template = (TEMPLATE_DIR / f"{prefix}-email-text.txt").read_text(encoding="utf-8")
    html_template = (TEMPLATE_DIR / f"{prefix}-email-html.html").read_text(encoding="utf-8")
    subject = subject_template.format(**values).strip()
    if any(character in subject for character in "\r\n"):
        raise ValueError("SUBJECT_HEADER_INJECTION")
    text = text_template.format(**values)
    html = html_template.format(**{key: escape(value, quote=True) for key, value in values.items()})
    return subject, text, html


class SmtpNotificationProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def deliver(self, address: str, payload: dict, delivery_id: str) -> ProviderResult:
        recipient = validate_email(address, self.settings.smtp_allowed_recipient_domains)
        subject, text, html = render_email(payload, delivery_id)
        if not self.settings.smtp_host or not self.settings.smtp_from_address:
            return ProviderResult(False, error_code="SMTP_NOT_CONFIGURED")
        if (
            not self.settings.smtp_use_tls
            and not self.settings.smtp_use_starttls
            and not (
                self.settings.environment == "development"
                and self.settings.smtp_allow_local_insecure
            )
        ):
            return ProviderResult(False, error_code="SMTP_TLS_REQUIRED")
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_address}>"
        message["To"] = recipient
        message.set_content(text)
        message.add_alternative(html, subtype="html")
        try:
            smtp_type = smtplib.SMTP_SSL if self.settings.smtp_use_tls else smtplib.SMTP
            with smtp_type(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=self.settings.smtp_timeout_seconds,
            ) as client:
                if self.settings.smtp_use_starttls and not self.settings.smtp_use_tls:
                    client.starttls()
                if self.settings.smtp_username:
                    client.login(self.settings.smtp_username, self.settings.smtp_password or "")
                refused = client.send_message(message)
                if refused:
                    code = next(iter(refused.values()))[0]
                    return ProviderResult(
                        False, 400 <= code < 500, code, error_code="SMTP_REJECTED"
                    )
            return ProviderResult(True, status_code=250)
        except smtplib.SMTPResponseException as exc:
            return ProviderResult(
                False, 400 <= exc.smtp_code < 500, exc.smtp_code, error_code="SMTP_RESPONSE"
            )
        except (OSError, smtplib.SMTPException):
            return ProviderResult(False, True, error_code="SMTP_CONNECTION")


def webhook_signature(secret: str, timestamp: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), timestamp.encode() + b"." + body, sha256).hexdigest()
    return f"v1={digest}"


def prepare_webhook_request(
    url: str,
    secret: str,
    payload: dict,
    delivery_id: str,
    idempotency_key: str,
    timestamp: str,
    settings: Settings,
) -> tuple[bytes, dict[str, str]]:
    """Validate, serialize and sign without opening a network connection."""
    validate_webhook_url(url, settings)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    if len(body) > settings.webhook_max_payload_bytes:
        raise ValueError("WEBHOOK_PAYLOAD_TOO_LARGE")
    return body, {
        "Content-Type": "application/json",
        "X-PliegoCheck-Delivery-Id": delivery_id,
        "X-PliegoCheck-Timestamp": timestamp,
        "X-PliegoCheck-Signature": webhook_signature(secret, timestamp, body),
        "X-PliegoCheck-Event": str(payload.get("event_type", "OPPORTUNITY_ALERT")),
        "X-PliegoCheck-Idempotency-Key": idempotency_key,
    }


def validate_webhook_url(url: str, settings: Settings) -> tuple[str, int]:
    parsed = urlsplit(url)
    if parsed.username or parsed.password or not parsed.hostname:
        raise ValueError("WEBHOOK_URL_INVALID")
    local_allowed = settings.environment == "development" and settings.webhook_allow_local_insecure
    if parsed.scheme != "https" and not (local_allowed and parsed.scheme == "http"):
        raise ValueError("WEBHOOK_HTTPS_REQUIRED")
    host = parsed.hostname.lower()
    if settings.webhook_allowed_hosts and host not in settings.webhook_allowed_hosts:
        raise ValueError("WEBHOOK_HOST_NOT_ALLOWED")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    for info in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global and not local_allowed:
            raise ValueError("WEBHOOK_ADDRESS_BLOCKED")
    return host, port


class SignedWebhookNotificationProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def deliver(
        self,
        url: str,
        secret: str,
        payload: dict,
        delivery_id: str,
        idempotency_key: str,
        timestamp: str,
    ) -> ProviderResult:
        try:
            body, headers = prepare_webhook_request(
                url, secret, payload, delivery_id, idempotency_key, timestamp, self.settings
            )
        except ValueError as exc:
            return ProviderResult(False, error_code=str(exc))
        try:
            with httpx.Client(
                timeout=self.settings.webhook_timeout_seconds,
                follow_redirects=False,
                max_redirects=self.settings.webhook_max_redirects,
            ) as client:
                response = client.post(url, content=body, headers=headers)
        except (httpx.TimeoutException, httpx.NetworkError):
            return ProviderResult(False, True, error_code="WEBHOOK_CONNECTION")
        code = response.status_code
        if 200 <= code < 300:
            return ProviderResult(True, status_code=code)
        retryable = code in {408, 425, 429} or 500 <= code < 600
        retry_after = None
        if code == 429 and response.headers.get("Retry-After", "").isdigit():
            retry_after = min(3600, int(response.headers["Retry-After"]))
        return ProviderResult(
            False, retryable, code, error_code=f"WEBHOOK_HTTP_{code}", retry_after=retry_after
        )
