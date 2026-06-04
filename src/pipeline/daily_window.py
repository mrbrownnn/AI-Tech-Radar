from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def report_date_for_timezone(app_timezone: str, *, now: datetime | None = None) -> date:
    timezone = ZoneInfo(app_timezone)
    current = now or datetime.now(timezone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone)
    else:
        current = current.astimezone(timezone)
    return current.date() - timedelta(days=1)


def report_window_utc(
    target_date: date,
    app_timezone: str,
) -> tuple[datetime, datetime]:
    timezone = ZoneInfo(app_timezone)
    start_local = datetime.combine(target_date, time.min, tzinfo=timezone)
    end_local = start_local + timedelta(days=1)
    return _to_utc_naive(start_local), _to_utc_naive(end_local)


def is_in_report_window(
    value: datetime | None,
    *,
    target_date: date,
    app_timezone: str,
) -> bool:
    if value is None:
        return False

    start, end = report_window_utc(target_date, app_timezone)
    comparable = _to_utc_naive(value)
    return start <= comparable < end


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
