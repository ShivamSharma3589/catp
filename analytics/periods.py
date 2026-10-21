from dataclasses import dataclass
from datetime import date, timedelta

from django.conf import settings
from rest_framework.exceptions import ValidationError

PRESETS = {
    'last_7_days': 7,
    'last_14_days': 14,
    'last_28_days': 28,
    'last_30_days': 30,
    'last_90_days': 90,
}


@dataclass(frozen=True)
class Period:
    start: date
    end: date

    @property
    def days(self):
        return (self.end - self.start).days + 1

    @property
    def previous(self):
        end = self.start - timedelta(days=1)
        return Period(start=end - timedelta(days=self.days - 1), end=end)

    def contains(self, day):
        return self.start <= day <= self.end

    def as_dict(self):
        return {'start': self.start.isoformat(), 'end': self.end.isoformat(), 'days': self.days}


def _parse_date(value, field):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError({field: 'Expected a date in YYYY-MM-DD format.'})


def resolve_period(params, anchor):
    anchor = anchor or date.today()
    date_from = params.get('date_from')
    date_to = params.get('date_to')

    if date_from or date_to:
        if not (date_from and date_to):
            raise ValidationError('date_from and date_to must be supplied together.')
        start = _parse_date(date_from, 'date_from')
        end = _parse_date(date_to, 'date_to')
        if start > end:
            raise ValidationError({'date_from': 'Must not be after date_to.'})
        if (end - start).days + 1 > settings.REPORTING['MAX_RANGE_DAYS']:
            raise ValidationError(
                f"Range exceeds {settings.REPORTING['MAX_RANGE_DAYS']} days."
            )
        return Period(start=start, end=end)

    preset = params.get('range') or settings.REPORTING['DEFAULT_RANGE']
    if preset not in PRESETS:
        raise ValidationError({'range': f'Unknown range. Use one of: {", ".join(PRESETS)}.'})
    length = PRESETS[preset]
    return Period(start=anchor - timedelta(days=length - 1), end=anchor)


def iso_weeks(period, count):
    end_week_start = period.end - timedelta(days=period.end.weekday())
    weeks = []
    for offset in range(count - 1, -1, -1):
        start = end_week_start - timedelta(weeks=offset)
        weeks.append((start, start + timedelta(days=6)))
    return weeks
