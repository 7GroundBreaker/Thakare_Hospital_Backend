"""Authoritative queue operations.

Every mutation runs in a transaction and locks the doctor row first, so
concurrent taps for one doctor are serialized; the unique constraints on
QueueToken are the final safety net. After a successful commit the waiting
room display is told to refresh (see realtime.py).
"""

from django.db import transaction
from django.utils import timezone

from hospital.models import Doctor

from . import realtime
from .models import MAX_TOKENS_PER_DAY, QueueToken, TokenStatus

UPCOMING_COUNT = 3


class QueueError(Exception):
    def __init__(self, message, status_code=409):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def today():
    return timezone.localdate()


def todays_tokens(doctor_id):
    return QueueToken.objects.filter(doctor_id=doctor_id, service_date=today())


def _lock_doctor(doctor_id):
    try:
        return Doctor.objects.select_for_update().get(pk=doctor_id)
    except Doctor.DoesNotExist:
        raise QueueError("Doctor not found.", 404)


def _validate_number(number):
    if not 1 <= number <= MAX_TOKENS_PER_DAY:
        raise QueueError(f"Token numbers run from 1 to {MAX_TOKENS_PER_DAY}.", 400)


def upcoming_numbers(tokens, count=UPCOMING_COUNT):
    """The next `count` uncalled numbers after the current/last-called one,
    wrapping around to pick up any earlier numbers that were skipped."""
    called = {t.number for t in tokens}
    serving = next((t for t in tokens if t.status == TokenStatus.SERVING), None)
    if serving:
        base = serving.number
    else:
        last = max(tokens, key=lambda t: t.called_at, default=None)
        base = last.number if last else 0
    ordered = list(range(base + 1, MAX_TOKENS_PER_DAY + 1)) + list(range(1, base + 1))
    return [n for n in ordered if n not in called][:count]


def _complete(token, now):
    token.status = TokenStatus.COMPLETED
    token.completed_at = now
    token.save(update_fields=["status", "completed_at"])


def call_number(doctor_id, number):
    """Make `number` the token being served. Whoever was being served is
    marked completed first. Re-calling an already completed number is
    allowed (e.g. a patient who stepped out and came back)."""
    _validate_number(number)
    with transaction.atomic():
        doctor = _lock_doctor(doctor_id)
        tokens = todays_tokens(doctor.id)
        current = tokens.filter(status=TokenStatus.SERVING).first()
        if current and current.number == number:
            return current
        now = timezone.now()
        if current:
            _complete(current, now)
        token, created = QueueToken.objects.get_or_create(
            doctor=doctor,
            service_date=today(),
            number=number,
            defaults={"status": TokenStatus.SERVING, "called_at": now},
        )
        if not created:
            token.status = TokenStatus.SERVING
            token.called_at = now
            token.completed_at = None
            token.save(update_fields=["status", "called_at", "completed_at"])
        realtime.notify_display_changed()
        return token


def call_next(doctor_id):
    with transaction.atomic():
        _lock_doctor(doctor_id)
        upcoming = upcoming_numbers(list(todays_tokens(doctor_id)), count=1)
        if not upcoming:
            raise QueueError(f"All {MAX_TOKENS_PER_DAY} tokens have been called today.")
        return call_number(doctor_id, upcoming[0])


def complete_current(doctor_id):
    with transaction.atomic():
        _lock_doctor(doctor_id)
        current = todays_tokens(doctor_id).filter(status=TokenStatus.SERVING).first()
        if current is None:
            raise QueueError("No token is being served.")
        _complete(current, timezone.now())
        realtime.notify_display_changed()
        return current


def mark_unexamined(doctor_id, number):
    """Flag a called token as not examined (patient absent / left). Works on
    the token being served or one already completed."""
    _validate_number(number)
    with transaction.atomic():
        _lock_doctor(doctor_id)
        token = todays_tokens(doctor_id).filter(number=number).first()
        if token is None:
            raise QueueError(f"Token {number} has not been called yet.")
        if token.status != TokenStatus.UNEXAMINED:
            token.status = TokenStatus.UNEXAMINED
            token.completed_at = timezone.now()
            token.save(update_fields=["status", "completed_at"])
            realtime.notify_display_changed()
        return token


def doctor_state(doctor):
    """Full state for the doctor's panel (staff only)."""
    tokens = list(todays_tokens(doctor.id).order_by("number"))
    serving = next((t for t in tokens if t.status == TokenStatus.SERVING), None)
    return {
        "doctor": {"id": doctor.id, "full_name": doctor.full_name},
        "service_date": today(),
        "max_tokens": MAX_TOKENS_PER_DAY,
        "serving": serving.number if serving else None,
        "upcoming": upcoming_numbers(tokens),
        "tokens": [
            {
                "number": t.number,
                "status": t.status,
                "called_at": t.called_at,
                "completed_at": t.completed_at,
            }
            for t in tokens
        ],
    }


def display_state():
    """Public waiting-room board: one entry per doctor who has called at
    least one token today. Token numbers and doctor name/room only."""
    tokens = list(
        QueueToken.objects.filter(service_date=today(), doctor__is_active=True).select_related(
            "doctor"
        )
    )
    by_doctor = {}
    for t in tokens:
        by_doctor.setdefault(t.doctor, []).append(t)
    boards = []
    for doctor in sorted(by_doctor, key=lambda d: (d.display_order, d.full_name)):
        doctor_tokens = by_doctor[doctor]
        serving = next((t for t in doctor_tokens if t.status == TokenStatus.SERVING), None)
        boards.append(
            {
                "doctor_id": doctor.id,
                "doctor_name": doctor.full_name,
                "room": doctor.clinic_location,
                "now_serving": serving.number if serving else None,
                "next_tokens": upcoming_numbers(doctor_tokens),
            }
        )
    return {"service_date": today(), "boards": boards}
