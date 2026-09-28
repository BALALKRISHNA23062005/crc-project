from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from members.models import Member
from .models import Event, Payment, Registration


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
