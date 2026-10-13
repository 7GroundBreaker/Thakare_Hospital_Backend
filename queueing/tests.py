import threading
from datetime import timedelta
from unittest import mock, skipUnless

from django.db import IntegrityError, connection, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Role, User
from hospital.models import Doctor

from . import services
from .models import QueueToken, TokenStatus


def make_user(username, role, doctor=None, is_staff=True, **extra):
    return User.objects.create_user(
        username=username,
        password="pw",
        role=role,
        doctor_profile=doctor,
        is_staff=is_staff,
        **extra,
    )


def statuses(doctor):
    return dict(services.todays_tokens(doctor.id).values_list("number", "status"))


class QueueTestBase(TestCase):
    def setUp(self):
        self.doctor = Doctor.objects.create(full_name="Dr. One", clinic_location="Room 4")
        self.other = Doctor.objects.create(full_name="Dr. Two", display_order=1)
        self.doc_user = make_user("doc1", Role.DOCTOR, self.doctor)
        self.client = APIClient(enforce_csrf_checks=True)


class ServiceTests(QueueTestBase):
    def test_tapping_a_number_serves_it_and_completes_previous(self):
        services.call_number(self.doctor.id, 5)
        services.call_number(self.doctor.id, 9)
        self.assertEqual(statuses(self.doctor), {5: "COMPLETED", 9: "SERVING"})
        five = QueueToken.objects.get(number=5)
        self.assertIsNotNone(five.completed_at)

    def test_tapping_current_number_is_a_no_op(self):
        first = services.call_number(self.doctor.id, 3)
        again = services.call_number(self.doctor.id, 3)
        self.assertEqual((first.pk, again.status), (again.pk, TokenStatus.SERVING))
        self.assertEqual(QueueToken.objects.count(), 1)

    def test_unexamined_then_call_again(self):
        services.call_number(self.doctor.id, 1)
        services.call_number(self.doctor.id, 2)
        services.mark_unexamined(self.doctor.id, 1)
        services.mark_unexamined(self.doctor.id, 2)
        self.assertEqual(statuses(self.doctor), {1: "UNEXAMINED", 2: "UNEXAMINED"})
        services.call_number(self.doctor.id, 1)
        self.assertEqual(statuses(self.doctor), {1: "SERVING", 2: "UNEXAMINED"})
        with self.assertRaises(services.QueueError):
            services.mark_unexamined(self.doctor.id, 50)

    def test_recalling_completed_number(self):
        services.call_number(self.doctor.id, 1)
        services.call_number(self.doctor.id, 2)
        token = services.call_number(self.doctor.id, 1)
        self.assertEqual(statuses(self.doctor), {1: "SERVING", 2: "COMPLETED"})
        self.assertIsNone(token.completed_at)

    def test_numbers_outside_1_to_100_rejected(self):
        for n in (0, 101):
            with self.assertRaises(services.QueueError) as ctx:
                services.call_number(self.doctor.id, n)
            self.assertEqual(ctx.exception.status_code, 400)

    def test_call_next_follows_sequence_and_wraps_to_skipped(self):
        self.assertEqual(services.call_next(self.doctor.id).number, 1)
        services.call_number(self.doctor.id, 99)
        self.assertEqual(services.call_next(self.doctor.id).number, 100)
        # After 100 it wraps around to the lowest number not yet called.
        self.assertEqual(services.call_next(self.doctor.id).number, 2)

    def test_call_next_when_all_called(self):
        today = services.today()
        now = timezone.now()
        QueueToken.objects.bulk_create(
            QueueToken(doctor=self.doctor, service_date=today, number=n,
                       status=TokenStatus.COMPLETED, called_at=now)
            for n in range(1, 101)
        )
        with self.assertRaises(services.QueueError):
            services.call_next(self.doctor.id)

    def test_complete_current(self):
        with self.assertRaises(services.QueueError):
            services.complete_current(self.doctor.id)
        services.call_number(self.doctor.id, 4)
        services.complete_current(self.doctor.id)
        self.assertEqual(statuses(self.doctor), {4: "COMPLETED"})
        # Next continues after the last called number even with nobody serving.
        self.assertEqual(services.doctor_state(self.doctor)["upcoming"], [5, 6, 7])

    def test_numbering_restarts_each_day_and_history_is_kept(self):
        services.call_number(self.doctor.id, 7)
        QueueToken.objects.update(service_date=services.today() - timedelta(days=1))
        self.assertEqual(services.call_next(self.doctor.id).number, 1)
        self.assertEqual(QueueToken.objects.count(), 2)

    def test_queues_are_independent_per_doctor(self):
        services.call_number(self.doctor.id, 5)
        services.call_number(self.other.id, 5)
        self.assertEqual(statuses(self.doctor), {5: "SERVING"})
        self.assertEqual(statuses(self.other), {5: "SERVING"})

    def test_database_rejects_duplicate_number(self):
        services.call_number(self.doctor.id, 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            QueueToken.objects.create(doctor=self.doctor, service_date=services.today(),
                                      number=1, status="COMPLETED", called_at=timezone.now())

    def test_database_rejects_two_serving_tokens(self):
        services.call_number(self.doctor.id, 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            QueueToken.objects.create(doctor=self.doctor, service_date=services.today(),
                                      number=2, status="SERVING", called_at=timezone.now())


class PanelApiTests(QueueTestBase):
    def login(self, user):
        self.client.force_login(user)
        # Prime the CSRF cookie the way the admin page does.
        self.client.get(reverse("token-panel"))
        self.client.credentials(HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value)

    def test_anonymous_is_rejected(self):
        self.assertIn(self.client.get(reverse("queue")).status_code, (401, 403))
        self.assertIn(self.client.post(reverse("queue-call-next")).status_code, (401, 403))

    def test_csrf_is_enforced(self):
        self.client.force_login(self.doc_user)
        self.assertEqual(self.client.post(reverse("queue-call", args=[1])).status_code, 403)
        self.assertFalse(QueueToken.objects.exists())

    def test_doctor_flow(self):
        self.login(self.doc_user)
        r = self.client.post(reverse("queue-call", args=[12]))
        self.assertEqual((r.status_code, r.data["serving"], r.data["upcoming"]), (200, 12, [13, 14, 15]))
        r = self.client.post(reverse("queue-call-next"))
        self.assertEqual(r.data["serving"], 13)
        r = self.client.post(reverse("queue-complete"))
        self.assertIsNone(r.data["serving"])
        self.assertEqual(self.client.post(reverse("queue-complete")).status_code, 409)
        r = self.client.get(reverse("queue"))
        self.assertEqual([(t["number"], t["status"]) for t in r.data["tokens"]],
                         [(12, "COMPLETED"), (13, "COMPLETED")])
        self.assertEqual(r.data["max_tokens"], 100)

    def test_doctor_cannot_manage_another_doctors_queue(self):
        self.login(self.doc_user)
        r = self.client.post(reverse("queue-call", args=[1]) + f"?doctor={self.other.id}")
        self.assertEqual(r.status_code, 403)
        self.assertFalse(QueueToken.objects.exists())

    def test_non_staff_and_unlinked_users_rejected(self):
        for user in (
            make_user("nostaff", Role.DOCTOR, self.other, is_staff=False),
            make_user("unlinked", Role.DOCTOR),
            make_user("editor", Role.CONTENT_EDITOR),
        ):
            self.client.force_login(user)
            self.assertEqual(
                self.client.get(reverse("queue"), {"doctor": self.doctor.id}).status_code, 403
            )

    def test_receptionist_must_choose_doctor(self):
        self.login(make_user("recep", Role.RECEPTIONIST))
        self.assertEqual(self.client.get(reverse("queue")).status_code, 403)
        r = self.client.post(reverse("queue-call", args=[3]) + f"?doctor={self.other.id}")
        self.assertEqual((r.status_code, r.data["serving"]), (200, 3))


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class AdminIntegrationTests(QueueTestBase):
    def test_doctor_lands_on_token_panel_after_admin_login(self):
        self.client.force_login(self.doc_user)
        r = self.client.get("/admin/")
        self.assertRedirects(r, reverse("token-panel"), fetch_redirect_response=False)
        page = self.client.get(reverse("token-panel"))
        self.assertContains(page, "Token Panel")
        self.assertContains(page, "Dr. One")

    def test_admin_sees_normal_index_with_panel_link(self):
        admin = User.objects.create_superuser("boss", "b@x.com", "pw")
        self.client.force_login(admin)
        r = self.client.get("/admin/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, reverse("token-panel"))

    def test_panel_requires_login_and_permission(self):
        r = self.client.get(reverse("token-panel"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"])
        self.client.force_login(make_user("editor", Role.CONTENT_EDITOR))
        self.assertEqual(self.client.get(reverse("token-panel")).status_code, 403)


class PublicDisplayTests(QueueTestBase):
    def test_board_shows_serving_and_next_three_only(self):
        services.call_number(self.doctor.id, 12)
        services.call_number(self.doctor.id, 14)  # 12 completed, 13 skipped for now
        services.call_number(self.other.id, 1)
        r = APIClient().get(reverse("queue-display"))
        self.assertEqual(r.status_code, 200)
        boards = r.data["boards"]
        self.assertEqual(
            boards[0],
            {"doctor_id": self.doctor.id, "doctor_name": "Dr. One", "room": "Room 4",
             "now_serving": 14, "next_tokens": [15, 16, 17]},
        )
        self.assertEqual(boards[1]["now_serving"], 1)
        self.assertEqual(set(r.data), {"service_date", "boards"})

    def test_board_never_contains_patient_or_staff_data(self):
        services.call_number(self.doctor.id, 1)
        body = APIClient().get(reverse("queue-display")).content.decode()
        for forbidden in ("patient", "phone", "mobile", "email", "doc1", "called_at"):
            self.assertNotIn(forbidden, body)

    def test_empty_board(self):
        r = APIClient().get(reverse("queue-display"))
        self.assertEqual(r.data["boards"], [])


@override_settings(SUPABASE_URL="https://example.supabase.co", SUPABASE_SERVICE_ROLE_KEY="k")
class RealtimeTests(QueueTestBase):
    def test_broadcast_sent_after_commit_with_no_patient_data(self):
        with mock.patch("queueing.realtime.urllib.request.urlopen") as urlopen:
            with self.captureOnCommitCallbacks(execute=True):
                services.call_number(self.doctor.id, 8)
        req = urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://example.supabase.co/realtime/v1/api/broadcast")
        self.assertIn(b'"topic": "queue-display"', req.data)
        self.assertIn(b'"payload": {}', req.data)

    def test_no_broadcast_when_operation_fails(self):
        with mock.patch("queueing.realtime.urllib.request.urlopen") as urlopen:
            with self.captureOnCommitCallbacks(execute=True):
                with self.assertRaises(services.QueueError):
                    services.complete_current(self.doctor.id)
        urlopen.assert_not_called()

    def test_broadcast_failure_does_not_break_request(self):
        with mock.patch("queueing.realtime.urllib.request.urlopen", side_effect=OSError("down")):
            with self.captureOnCommitCallbacks(execute=True):
                services.call_number(self.doctor.id, 2)
        self.assertEqual(statuses(self.doctor), {2: "SERVING"})


@skipUnless(connection.vendor == "postgresql", "row-level locking needs PostgreSQL")
class ConcurrencyTests(TransactionTestCase):
    def run_threads(self, target, count):
        def wrapped():
            try:
                target()
            except services.QueueError:
                pass
            finally:
                connection.close()

        threads = [threading.Thread(target=wrapped) for _ in range(count)]
        [t.start() for t in threads]
        [t.join() for t in threads]

    def test_concurrent_taps_leave_exactly_one_serving(self):
        doctor = Doctor.objects.create(full_name="Dr. C")
        numbers = iter(range(1, 11))
        lock = threading.Lock()

        def tap():
            with lock:
                n = next(numbers)
            services.call_number(doctor.id, n)

        self.run_threads(tap, 10)
        self.assertEqual(services.todays_tokens(doctor.id).filter(status="SERVING").count(), 1)
        self.assertEqual(services.todays_tokens(doctor.id).count(), 10)

    def test_concurrent_call_next_never_duplicates(self):
        doctor = Doctor.objects.create(full_name="Dr. D")
        self.run_threads(lambda: services.call_next(doctor.id), 8)
        numbers = sorted(services.todays_tokens(doctor.id).values_list("number", flat=True))
        self.assertEqual(numbers, list(range(1, 9)))
