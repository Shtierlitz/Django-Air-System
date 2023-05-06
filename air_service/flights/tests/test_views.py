

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class TestViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='test_username_1', first_name='test_first_name_1',
                                              last_name='test_last_name_1',
                                              email_verify=True,
                                              password='test_password')
        self.client.login(username='test_username_1', password='test_password')

    def test_RegisterUser_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_RegisterUser_post(self):
        response = self.client.post(reverse('register'), {
            'username': 'test_username',
            'email': 'test@email.com',
            'password1': 'register_test_password_007',
            'password2': 'register_test_password_007',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(User.objects.all()), 2)

    def test_LoginUser_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_LoginUser_post(self):
        response = self.client.post(reverse('login'), {
            'username': 'test_username_1',
            'password': 'test_password'
        })
        self.assertEqual(response.status_code, 302)

    def test_ConfirmEmailView(self):
        response = self.client.get(reverse('confirm_email'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/confirm_email.html')

    def test_InvalidVerifyView(self):
        response = self.client.get(reverse('invalid_verify'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/invalid_verify.html')

    def test_EmailVerify(self):
        response = self.client.get(reverse('verify_email', args=[1, 2]))
        self.assertEqual(response.status_code, 302)