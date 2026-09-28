from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class NavigationTests(TestCase):
	def test_home_redirects_to_events(self):
		response = self.client.get('/')

		self.assertRedirects(response, '/events/', fetch_redirect_response=False)

	def test_logged_out_navigation_shows_login_and_signup(self):
		response = self.client.get('/events/')

		self.assertContains(response, 'Events')
		self.assertContains(response, 'My Registrations')
		self.assertContains(response, reverse('login'))
		self.assertContains(response, reverse('signup'))
		self.assertNotContains(response, 'Logout')

	def test_logged_in_navigation_uses_post_logout_form(self):
		user = User.objects.create_user(username='runner', password='password')
		self.client.force_login(user)

		response = self.client.get('/events/')

		self.assertContains(response, 'Events')
		self.assertContains(response, 'My Registrations')
		self.assertContains(response, f'action="{reverse("logout")}" method="post"')
		self.assertNotContains(response, 'Sign Up')
		self.assertEqual(self.client.get(reverse('logout')).status_code, 405)


class SignupValidationTests(TestCase):
	def test_duplicate_email_shows_friendly_validation_error(self):
		user = User.objects.create_user(username='existing', password='password')
		from .models import Member
		Member.objects.create(
			user=user,
			name='Existing Member',
			email='runner@example.com',
			phone='9876543210',
		)

		response = self.client.post(reverse('signup'), {
			'username': 'newrunner',
			'password': 'password123',
			'name': 'New Runner',
			'email': 'RUNNER@example.com',
			'phone': '9876543211',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'An account with this email already exists.')
		self.assertFalse(User.objects.filter(username='newrunner').exists())

	def test_invalid_phone_shows_validation_error(self):
		response = self.client.post(reverse('signup'), {
			'username': 'newrunner',
			'password': 'password123',
			'name': 'New Runner',
			'email': 'newrunner@example.com',
			'phone': '12345',
		})

		self.assertContains(response, 'Enter a valid 10-digit Indian mobile number.')
		self.assertFalse(User.objects.filter(username='newrunner').exists())
