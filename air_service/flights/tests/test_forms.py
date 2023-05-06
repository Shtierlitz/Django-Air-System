from django.contrib.auth import get_user_model
from django.test import TestCase

from flights.forms import RegisterUserForm, LoginUserForm

User = get_user_model()


class TestForms(TestCase):

    def test_RegisterForm_is_valid(self):
        form = RegisterUserForm(data={
            'username': 'test_username_1',
            'email': "test_email@mail.com",
            'password1': 'test_password',
            'password2': 'test_password'
        })
        self.assertTrue(form.is_valid())

    def test_RegisterForm_no_data(self):
        form = RegisterUserForm(
            data={})
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 4)

    def test_RegisterForm_clean_fields(self):
        form = RegisterUserForm(data={
            'username': 'u' * 151,
            'email': "test_email",
            'password1': '1234_test_true',
            'password2': '1234_test_false'
        })
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 3)

    def test_LoginForm_is_valid(self):
        self.user1 = User.objects.create_user(username='test_username_1', first_name='test_first_name_1',
                                              last_name='test_last_name_1', email_verify=True,
                                              password='test_password')
        form = LoginUserForm(data={
            'username': 'test_username_1',
            'password': 'test_password'
        })
        self.assertTrue(form.is_valid())

    def test_LoginForm_no_data(self):
        form = LoginUserForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 2)

    def test_LoginForm_clean_passwords(self):
        form = LoginUserForm(data={
            'password': '1234'  # to short
        })
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
