from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from hospital.notifications import NotificationService

from .models import Appointment

_STATUS_CACHE_ATTR = "_previous_status"


@receiver(pre_save, sender=Appointment)
def cache_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            previous = Appointment.objects.get(pk=instance.pk)
            setattr(instance, _STATUS_CACHE_ATTR, previous.status)
        except Appointment.DoesNotExist:
            setattr(instance, _STATUS_CACHE_ATTR, None)
    else:
        setattr(instance, _STATUS_CACHE_ATTR, None)


@receiver(post_save, sender=Appointment)
def notify_on_change(sender, instance, created, **kwargs):
    if created:
        NotificationService.notify_appointment_requested(instance)
        return
    previous_status = getattr(instance, _STATUS_CACHE_ATTR, None)
    if previous_status and previous_status != instance.status:
        NotificationService.notify_appointment_status_changed(instance, previous_status)
