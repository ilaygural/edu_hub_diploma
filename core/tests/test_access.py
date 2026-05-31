from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Teacher

User = get_user_model()


class AnonymousAccessTests(TestCase):
  def setUp(self):
    self.client = Client()

  def test_manager_reports_redirects_to_login(self):
    response = self.client.get(reverse('manager_reports'))
    self.assertEqual(response.status_code, 302)
    self.assertIn(reverse('users:login'), response.url)

  def test_teacher_ktp_redirects_to_login(self):
    response = self.client.get(reverse('teacher_ktp'))
    self.assertEqual(response.status_code, 302)
    self.assertIn(reverse('users:login'), response.url)


class RoleAccessTests(TestCase):
  def setUp(self):
    self.user = User.objects.create_user(
      username='teacher_only',
      password='pass12345',
    )
    Teacher.objects.create(user=self.user, patronymic='Иванович')
    self.client = Client()
    self.client.login(username='teacher_only', password='pass12345')

  def test_teacher_cannot_open_parent_dashboard(self):
    response = self.client.get(reverse('parent_dashboard'))
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response.url, reverse('users:role_select'))

  def test_role_select_shows_all_role_buttons(self):
    response = self.client.get(reverse('users:role_select'))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Родитель')
    self.assertContains(response, 'Педагог')
    self.assertContains(response, 'Менеджер')
