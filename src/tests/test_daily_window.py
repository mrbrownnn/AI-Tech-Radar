from datetime import date, datetime

from src.pipeline.daily_window import (
    is_in_report_window,
    report_date_for_timezone,
    report_window_utc,
)


def test_report_date_is_previous_local_day():
    target_date = report_date_for_timezone(
        "Asia/Bangkok",
        now=datetime(2026, 6, 4, 9, 0),
    )

    assert target_date == date(2026, 6, 3)


def test_report_window_uses_app_timezone_in_utc_bounds():
    start, end = report_window_utc(date(2026, 6, 3), "Asia/Bangkok")

    assert start == datetime(2026, 6, 2, 17, 0)
    assert end == datetime(2026, 6, 3, 17, 0)
    assert is_in_report_window(
        datetime(2026, 6, 3, 16, 59),
        target_date=date(2026, 6, 3),
        app_timezone="Asia/Bangkok",
    )
    assert not is_in_report_window(
        datetime(2026, 6, 3, 17, 0),
        target_date=date(2026, 6, 3),
        app_timezone="Asia/Bangkok",
    )
