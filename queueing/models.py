from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from hospital.models import Doctor

MAX_TOKENS_PER_DAY = 100


class TokenStatus(models.TextChoices):
    SERVING = "SERVING", "Serving"
    COMPLETED = "COMPLETED", "Completed"


class QueueToken(models.Model):
    """A token number (1..100) that a doctor has called on a given day.

    Patients receive pre-printed numbers at reception, so all 100 numbers
    are implicitly "waiting" each day; a row is only written once the doctor
    calls a number. Rows are never deleted, so past days remain as history
    and numbering restarts each service date.
    """

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="queue_tokens")
    service_date = models.DateField(db_index=True)
    number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(MAX_TOKENS_PER_DAY)]
    )
    status = models.CharField(max_length=10, choices=TokenStatus.choices)
    called_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-service_date", "doctor", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "service_date", "number"], name="uniq_token_number_per_day"
            ),
            # At most one token can be SERVING per doctor per day.
            models.UniqueConstraint(
                fields=["doctor", "service_date"],
                condition=models.Q(status="SERVING"),
                name="uniq_serving_token_per_day",
            ),
            models.CheckConstraint(
                condition=models.Q(number__gte=1, number__lte=MAX_TOKENS_PER_DAY),
                name="token_number_1_to_100",
            ),
        ]

    def __str__(self):
        return f"{self.doctor} #{self.number} ({self.service_date}, {self.status})"
