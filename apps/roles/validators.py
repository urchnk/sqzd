from datetime import time

from django.forms import ValidationError


def validate_schedule(values: dict[str, time]):
    start = end = None
    for k, v in values:
        if k == "start":
            start = values
        elif k == "end":
            end = values
        else:
            raise ValidationError(f"Key '{k}' is not allowed, must be 'start' or 'end'")
    if start >= end:
        raise ValidationError("Start time must be less than end time, obviously.")
