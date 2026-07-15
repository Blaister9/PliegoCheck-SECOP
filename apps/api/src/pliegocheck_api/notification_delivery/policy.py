"""Políticas puras de selección, quiet hours y reintentos."""
# mypy: disable-error-code="no-untyped-def,no-any-return"

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from zoneinfo import ZoneInfo

SEVERITY_RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def subscription_matches(subscription, alert) -> bool:
    return bool(
        subscription.enabled
        and (subscription.monitor_id is None or subscription.monitor_id == alert.monitor_id)
        and (not subscription.alert_types or alert.alert_type in subscription.alert_types)
        and SEVERITY_RANK.get(alert.severity, 0)
        >= SEVERITY_RANK.get(subscription.minimum_severity, 0)
    )


def quiet_hours_end(subscription, severity: str, now: datetime) -> datetime | None:
    config = subscription.quiet_hours
    if not config or (severity == "CRITICAL" and config.get("critical_bypass", True)):
        return None
    zone = ZoneInfo(subscription.timezone)
    local = now.astimezone(zone)
    start_h, start_m = map(int, config["start"].split(":"))
    end_h, end_m = map(int, config["end"].split(":"))
    start = local.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = local.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    if end <= start:
        if local < end:
            start -= timedelta(days=1)
        else:
            end += timedelta(days=1)
    if start <= local < end:
        return end.astimezone(UTC)
    return None


def digest_period_bounds(period: str, timezone: str, now: datetime) -> tuple[datetime, datetime]:
    """Return the last fully closed local day or week as stable UTC boundaries."""
    zone = ZoneInfo(timezone)
    local_now = now.astimezone(zone)
    end = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "WEEKLY":
        end -= timedelta(days=end.weekday())
        start = end - timedelta(days=7)
    else:
        start = end - timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def retry_delay_seconds(attempt: int, base: int, maximum: int, jitter: int, seed: str) -> int:
    bounded = min(maximum, base * (2 ** max(0, attempt - 1)))
    if not jitter:
        return bounded
    deterministic = int(sha256(f"{seed}:{attempt}".encode()).hexdigest()[:8], 16)
    return min(maximum, bounded + deterministic % (jitter + 1))


def parse_retry_after(value: str | None, maximum: int) -> int | None:
    if not value or not value.strip().isdigit():
        return None
    return min(maximum, max(0, int(value.strip())))
