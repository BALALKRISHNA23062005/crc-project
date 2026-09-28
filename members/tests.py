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
