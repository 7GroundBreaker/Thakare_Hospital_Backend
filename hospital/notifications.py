"""Notification abstraction (spec section 44/45).

NotificationService fans out to whichever providers are configured, so a
provider can be swapped (e.g. a real WhatsApp Business API integration)
without touching call sites in appointments/content views. Nothing here
raises on a missing provider config — notifications are best-effort and
must never block the patient-facing request (e.g. an appointment booking
succeeds even if the email backend is down).
"""

import logging

from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger("thakare_hospital")


class EmailNotificationProvider:
    def send(self, *, to, subject, template_name, context):
        if not to:
            return
        from django.core.mail import send_mail

        try:
            body = render_to_string(f"emails/{template_name}.txt", context)
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to] if isinstance(to, str) else list(to),
                fail_silently=True,
            )
        except Exception:
            logger.exception("Failed to send email notification (template=%s)", template_name)


class WhatsAppNotificationProvider:
    """Stub provider. Wire up a real WhatsApp Business API client here and
    flip WHATSAPP_PROVIDER_ENABLED=true when credentials are available."""

    def send(self, *, to, template_name, context):
        if not settings.WHATSAPP_PROVIDER_ENABLED:
            logger.info("WhatsApp notification skipped (provider disabled): %s", template_name)
            return
        # TODO: integrate with the configured WhatsApp Business API provider
        # using settings.WHATSAPP_API_URL / settings.WHATSAPP_API_TOKEN.
        logger.info("WhatsApp notification queued: %s -> %s", template_name, to)


class SMSNotificationProvider:
    """Placeholder for a future SMS integration — intentionally a no-op."""

    def send(self, *, to, template_name, context):
        logger.debug("SMS notifications are not yet implemented (template=%s)", template_name)


class NotificationService:
    email = EmailNotificationProvider()
    whatsapp = WhatsAppNotificationProvider()
    sms = SMSNotificationProvider()

    @classmethod
    def notify_appointment_requested(cls, appointment):
        cls.email.send(
            to=appointment.patient.email,
            subject=f"Appointment request received — {appointment.reference_id}",
            template_name="appointment_requested",
            context={"appointment": appointment},
        )
        if settings.HOSPITAL_ADMIN_NOTIFICATION_EMAIL:
            cls.email.send(
                to=settings.HOSPITAL_ADMIN_NOTIFICATION_EMAIL,
                subject=f"New appointment request — {appointment.reference_id}",
                template_name="admin_new_appointment",
                context={"appointment": appointment},
            )
        cls.whatsapp.send(to=appointment.patient.mobile_number, template_name="appointment_requested", context={"appointment": appointment})

    @classmethod
    def notify_appointment_status_changed(cls, appointment, previous_status):
        status_template_map = {
            "CONFIRMED": "appointment_confirmed",
            "RESCHEDULED": "appointment_rescheduled",
            "CANCELLED": "appointment_cancelled",
        }
        template_name = status_template_map.get(appointment.status)
        if not template_name:
            return
        cls.email.send(
            to=appointment.patient.email,
            subject=f"Appointment {appointment.get_status_display()} — {appointment.reference_id}",
            template_name=template_name,
            context={"appointment": appointment},
        )
        cls.whatsapp.send(to=appointment.patient.mobile_number, template_name=template_name, context={"appointment": appointment})

    @classmethod
    def notify_contact_enquiry(cls, enquiry):
        if settings.HOSPITAL_ADMIN_NOTIFICATION_EMAIL:
            cls.email.send(
                to=settings.HOSPITAL_ADMIN_NOTIFICATION_EMAIL,
                subject=f"New website enquiry from {enquiry.name}",
                template_name="admin_new_enquiry",
                context={"enquiry": enquiry},
            )
        cls.email.send(
            to=enquiry.email,
            subject="We received your message — Thakare Hospital",
            template_name="contact_enquiry",
            context={"enquiry": enquiry},
        )
