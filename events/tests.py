from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from razorpay.errors import SignatureVerificationError

from members.models import Member
from .models import Attendance, Event, Payment, Registration


class EventFeeTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='runner', password='password')
		self.member = Member.objects.create(
			user=self.user,
			name='Runner',
			email='runner@example.com',
			phone='1234567890',
		)
		self.event = Event.objects.create(
			title='Run',
			date='2026-10-01',
			location='Hubli',
			max_participants=10,
			fee=Decimal('25.50'),
		)
		self.client.force_login(self.user)

	def test_free_event_registration_is_paid_and_shows_payment_not_applicable(self):
		self.event.fee = Decimal('0.00')
		self.event.save()

		response = self.client.post(
			reverse('register_for_event'),
			{'event': self.event.id},
			follow=True,
		)

		registration = Registration.objects.get(member=self.member, event=self.event)
		self.assertEqual(registration.payment_status, 'paid')
		self.assertContains(response, 'Payment: Not applicable (free event).')
		self.assertNotContains(response, 'Pay Registration Fee')

	@patch('events.views.razorpay.Client')
	def test_initiate_payment_uses_event_fee_in_paise(self, client_class):
		registration = Registration.objects.create(member=self.member, event=self.event)
		client = client_class.return_value
		client.order.create.return_value = {'id': 'order_test'}

		response = self.client.get(reverse('initiate_payment', args=[registration.id]))

		client.order.create.assert_called_once_with({
			'amount': 2550,
			'currency': 'INR',
			'payment_capture': 1,
		})
		self.assertEqual(response.context['amount'], 2550)

	@patch('events.views.razorpay.Client')
	def test_payment_success_records_event_fee(self, client_class):
		registration = Registration.objects.create(
			member=self.member,
			event=self.event,
			razorpay_order_id='order_test',
		)
		client = client_class.return_value

		response = self.client.get(reverse('payment_success', args=[registration.id]), {
			'razorpay_payment_id': 'payment_test',
			'razorpay_order_id': 'order_test',
			'razorpay_signature': 'signature_test',
		})

		self.assertEqual(response.status_code, 200)
		payment = Payment.objects.get(registration=registration)
		self.assertEqual(payment.amount, Decimal('25.50'))
		client.utility.verify_payment_signature.assert_called_once()


class MyRegistrationsTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='runner', password='password')
		self.member = Member.objects.create(
			user=self.user,
			name='Runner',
			email='runner@example.com',
			phone='1234567890',
		)
		self.other_user = User.objects.create_user(username='other', password='password')
		self.other_member = Member.objects.create(
			user=self.other_user,
			name='Other Runner',
			email='other@example.com',
			phone='1234567891',
		)
		self.event = Event.objects.create(
			title='Own event',
			date='2026-10-01',
			location='Hubli',
			max_participants=10,
			fee=Decimal('25.50'),
		)
		self.pending_registration = Registration.objects.create(
			member=self.member,
			event=self.event,
		)
		self.paid_registration = Registration.objects.create(
			member=self.member,
			event=self.event,
			payment_status='paid',
		)
		self.other_event = Event.objects.create(
			title='Other event',
			date='2026-10-02',
			location='Dharwad',
			max_participants=10,
		)
		Registration.objects.create(member=self.other_member, event=self.other_event)
		self.client.force_login(self.user)

	def test_page_shows_only_own_registrations_and_pending_pay_link(self):
		response = self.client.get(reverse('my_registrations'))

		self.assertContains(response, 'Own event')
		self.assertNotContains(response, 'Other event')
		self.assertContains(response, reverse('qr_code_image', args=[self.pending_registration.id]))
		self.assertContains(response, reverse('initiate_payment', args=[self.pending_registration.id]))
		self.assertNotContains(response, reverse('initiate_payment', args=[self.paid_registration.id]))

	def test_page_requires_login(self):
		self.client.logout()

		response = self.client.get(reverse('my_registrations'))

		self.assertRedirects(
			response,
			f"{reverse('login')}?next={reverse('my_registrations')}",
			fetch_redirect_response=False,
		)


class OrganizerEventTests(TestCase):
	def setUp(self):
		self.staff_user = User.objects.create_user(
			username='organizer', password='password', is_staff=True,
		)
		self.member_user = User.objects.create_user(username='runner', password='password')
		self.member = Member.objects.create(
			user=self.member_user,
			name='Runner',
			email='runner@example.com',
			phone='1234567890',
		)
		self.event = Event.objects.create(
			title='Club run',
			date='2026-10-01',
			location='Hubli',
			max_participants=10,
		)
		self.paid_registration = Registration.objects.create(
			member=self.member,
			event=self.event,
			payment_status='paid',
		)
		Registration.objects.create(member=self.member, event=self.event)

	def test_staff_sees_registrations_status_and_counts(self):
		Attendance.objects.create(registration=self.paid_registration)
		self.client.force_login(self.staff_user)

		response = self.client.get(reverse('organizer_event', args=[self.event.id]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Runner')
		self.assertContains(response, 'runner@example.com')
		self.assertContains(response, 'Registrations</dt>\n    <dd class="col-sm-9">2')
		self.assertContains(response, 'Paid</dt>\n    <dd class="col-sm-9">1')
		self.assertContains(response, 'Checked in</dt>\n    <dd class="col-sm-9">1')
		self.assertContains(response, 'Checked in')
		self.assertContains(response, 'Not checked in')

	def test_non_staff_cannot_view_organizer_page(self):
		self.client.force_login(self.member_user)

		response = self.client.get(reverse('organizer_event', args=[self.event.id]))

		self.assertEqual(response.status_code, 403)


class EventListTests(TestCase):
	def test_event_list_only_shows_today_and_future_events(self):
		today = timezone.localdate()
		Event.objects.create(
			title='Past run',
			date=today - timedelta(days=1),
			location='Hubli',
			max_participants=10,
		)
		Event.objects.create(
			title='Upcoming run',
			date=today,
			location='Dharwad',
			max_participants=10,
		)

		response = self.client.get(reverse('event_list'))

		self.assertNotContains(response, 'Past run')
		self.assertContains(response, 'Upcoming run')


class RegistrationBlockingTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='runner', password='password')
		self.member = Member.objects.create(
			user=self.user,
			name='Runner',
			email='runner@example.com',
			phone='1234567890',
		)
		self.event = Event.objects.create(
			title='Club run',
			date='2026-10-01',
			location='Hubli',
			max_participants=1,
		)
		self.client.force_login(self.user)

	def test_duplicate_registration_shows_friendly_error(self):
		Registration.objects.create(member=self.member, event=self.event)

		response = self.client.post(reverse('register_for_event'), {'event': self.event.id})

		self.assertEqual(response.context['error'], "You're already registered for this event.")
		self.assertEqual(Registration.objects.filter(event=self.event).count(), 1)

	def test_full_event_shows_friendly_error(self):
		other_user = User.objects.create_user(username='other', password='password')
		other_member = Member.objects.create(
			user=other_user,
			name='Other Runner',
			email='other@example.com',
			phone='1234567891',
		)
		Registration.objects.create(member=other_member, event=self.event)

		response = self.client.post(reverse('register_for_event'), {'event': self.event.id})

		self.assertContains(response, 'Sorry, this event is full.')
		self.assertEqual(Registration.objects.filter(event=self.event).count(), 1)


class RegistrationOwnershipTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username='owner', password='password')
		self.owner_member = Member.objects.create(
			user=self.owner,
			name='Owner',
			email='owner@example.com',
			phone='1234567890',
		)
		other_user = User.objects.create_user(username='other', password='password')
		Member.objects.create(
			user=other_user,
			name='Other',
			email='other@example.com',
			phone='1234567891',
		)
		self.event = Event.objects.create(
			title='Club run',
			date='2026-10-01',
			location='Hubli',
			max_participants=10,
			fee=Decimal('25.00'),
		)
		self.registration = Registration.objects.create(
			member=self.owner_member,
			event=self.event,
			razorpay_order_id='order_test',
		)
		self.client.force_login(other_user)

	@patch('events.views.razorpay.Client')
	def test_other_member_gets_404_for_registration_owned_routes(self, client_class):
		urls = [
			reverse('registration_success', args=[self.registration.id]),
			reverse('qr_code_image', args=[self.registration.id]),
			reverse('initiate_payment', args=[self.registration.id]),
			reverse('payment_success', args=[self.registration.id]),
		]

		for url in urls:
			with self.subTest(url=url):
				self.assertEqual(self.client.get(url).status_code, 404)

		client_class.assert_not_called()


class CheckinAccessTests(TestCase):
	def setUp(self):
		self.member_user = User.objects.create_user(username='runner', password='password')
		member = Member.objects.create(
			user=self.member_user,
			name='Runner',
			email='runner@example.com',
			phone='1234567890',
		)
		self.staff_user = User.objects.create_user(
			username='organizer', password='password', is_staff=True,
		)
		event = Event.objects.create(
			title='Club run',
			date='2026-10-01',
			location='Hubli',
			max_participants=10,
		)
		self.registration = Registration.objects.create(member=member, event=event)

	def test_non_staff_cannot_check_in(self):
		self.client.force_login(self.member_user)

		response = self.client.get(reverse('checkin', args=[self.registration.qr_code]))

		self.assertEqual(response.status_code, 403)
		self.assertFalse(Attendance.objects.filter(registration=self.registration).exists())

	def test_staff_can_check_in(self):
		self.client.force_login(self.staff_user)

		response = self.client.get(reverse('checkin', args=[self.registration.qr_code]))

		self.assertEqual(response.status_code, 200)
		self.assertTrue(Attendance.objects.filter(registration=self.registration).exists())


class PaymentSignatureRejectionTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='runner', password='password')
		member = Member.objects.create(
			user=self.user,
			name='Runner',
			email='runner@example.com',
			phone='1234567890',
		)
		event = Event.objects.create(
			title='Club run',
			date='2026-10-01',
			location='Hubli',
			max_participants=10,
			fee=Decimal('25.00'),
		)
		self.registration = Registration.objects.create(
			member=member,
			event=event,
			razorpay_order_id='order_test',
		)
		self.client.force_login(self.user)

	@patch('events.views.razorpay.Client')
	def test_invalid_signature_does_not_mark_registration_paid(self, client_class):
		client = client_class.return_value
		client.utility.verify_payment_signature.side_effect = SignatureVerificationError(
			'Invalid signature',
		)

		response = self.client.get(reverse('payment_success', args=[self.registration.id]), {
			'razorpay_payment_id': 'payment_test',
			'razorpay_order_id': 'order_test',
			'razorpay_signature': 'invalid_signature',
		})

		self.assertEqual(response.status_code, 400)
		self.assertContains(response, 'Payment verification failed.', status_code=400)
		self.registration.refresh_from_db()
		self.assertEqual(self.registration.payment_status, 'pending')
		self.assertFalse(Payment.objects.filter(registration=self.registration).exists())
