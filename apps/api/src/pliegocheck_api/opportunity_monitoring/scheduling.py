"""Cálculo puro, sin drift, de próximas ejecuciones."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from pliegocheck_schemas import OpportunityMonitorFrequency

_INTERVALS = {
    OpportunityMonitorFrequency.HOURLY: timedelta(hours=1),
    OpportunityMonitorFrequency.EVERY_3_HOURS: timedelta(hours=3),
    OpportunityMonitorFrequency.EVERY_6_HOURS: timedelta(hours=6),
    OpportunityMonitorFrequency.EVERY_12_HOURS: timedelta(hours=12),
    OpportunityMonitorFrequency.DAILY: timedelta(days=1),
}


def next_run_at(
    scheduled_for: datetime,
    frequency: OpportunityMonitorFrequency,
    timezone: str,
    *,
    now: datetime | None = None,
) -> datetime:
    """Devuelve el primer slot futuro; colapsa intervalos perdidos a uno."""
    current = (now or datetime.now(UTC)).astimezone(UTC)
    zone = ZoneInfo(timezone)
    candidate = scheduled_for.astimezone(zone)
    if frequency == OpportunityMonitorFrequency.WEEKDAYS:
        while True:
            candidate += timedelta(days=1)
            if candidate.weekday() < 5 and candidate.astimezone(UTC) > current:
                return candidate.astimezone(UTC)
    interval = _INTERVALS[frequency]
    candidate += interval
    if candidate.astimezone(UTC) <= current:
        missed = int((current - candidate.astimezone(UTC)) / interval) + 1
        candidate += interval * missed
    return candidate.astimezone(UTC)
