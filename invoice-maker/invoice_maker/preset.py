"""Auto-build a period invoice (1st-15th or 16th-end of month).

Working days are generated for the period, skipping weekends and
Australian public holidays for the configured state. Public holidays are
computed for whatever year the period falls in, so it keeps working every
year with no manual updates.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import List, Tuple

import holidays as holidays_lib

from .models import Config, Invoice, LineItem


def last_day_of_month(day: date) -> date:
    return day.replace(day=calendar.monthrange(day.year, day.month)[1])


def current_period(today: date) -> Tuple[date, date, int]:
    """Return (start, end, half) for the period that ``today`` falls in.

    Days 1-15  -> first half  (invoice generated on the 15th).
    Days 16-EOM -> second half (invoice generated on the last day).
    """
    if today.day <= 15:
        return today.replace(day=1), today.replace(day=15), 1
    return today.replace(day=16), last_day_of_month(today), 2


def public_holidays(state: str, years):
    """Australian public holidays for a state/territory across the given years."""
    return holidays_lib.country_holidays("AU", subdiv=state, years=list(years))


def working_days(
    start: date,
    end: date,
    state: str,
    exclude_weekends: bool = True,
    exclude_public_holidays: bool = True,
) -> List[date]:
    hols = (
        public_holidays(state, range(start.year, end.year + 1))
        if exclude_public_holidays
        else {}
    )
    days: List[date] = []
    current = start
    while current <= end:
        is_weekend = current.weekday() >= 5
        is_holiday = current in hols
        if not (exclude_weekends and is_weekend) and not (exclude_public_holidays and is_holiday):
            days.append(current)
        current += timedelta(days=1)
    return days


def build_preset_invoice(
    config: Config,
    as_of: date = None,
    start_override: date = None,
    end_override: date = None,
) -> Invoice:
    preset = config.preset
    today = as_of or date.today()
    start, end, half = current_period(today)

    natural_start, natural_end, _ = current_period(today)
    is_nonstandard = start_override and start_override != natural_start

    if start_override:
        start = start_override
    if end_override:
        end = end_override

    days = working_days(
        start,
        end,
        preset.state,
        preset.exclude_weekends,
        preset.exclude_public_holidays,
    )

    # If a fixed period rate is configured and no custom start was supplied
    # (i.e. this is a standard full half-month period), distribute the period
    # total evenly across working days. Custom start overrides mean it's a
    # partial/non-regular period, so fall back to the daily rate instead.
    if preset.period_rate > 0 and days and not is_nonstandard:
        per_day_rate = preset.period_rate / len(days)
        rate_type = "Bimonthly"
        invoice_rate = preset.period_rate
    else:
        per_day_rate = None  # falls back to invoice-level daily rate
        rate_type = preset.rate_type
        invoice_rate = preset.rate

    items = [
        LineItem(
            date=day,
            project=preset.default_project,
            episode=preset.default_episode,
            description=preset.default_description,
            sick_vacation_hrs=0.0,
            hours_worked=preset.hours_per_day,
            rate=per_day_rate,
        )
        for day in days
    ]

    number = f"{preset.invoice_number_prefix}{start.year}{start.month:02d}-{half}"

    return Invoice(
        invoice_number=number,
        invoice_date=end,
        rate_type=rate_type,
        currency=preset.currency,
        rate=invoice_rate,
        work_start_date=start,
        work_end_date=end,
        line_items=items,
        comments=preset.comments,
    )
