from datetime import date, datetime, timedelta


def difference(a: datetime, b: datetime) -> timedelta:
    return datetime.combine(date.today(), b.time()) - datetime.combine(date.today(), a.time())
