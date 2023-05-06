from django.test import SimpleTestCase
from django.urls import reverse, resolve
from flights.views import *


class TestUrls(SimpleTestCase):

    def test_RegisterUser(self):
        url = reverse('register')
        assert resolve(url).func.view_class == RegisterUser

    def test_LoginUser(self):
        url = reverse('login')
        assert resolve(url).func.view_class == LoginUser

    def test_EmailVerify(self):
        url = reverse('verify_email', args=[1, 2])
        assert resolve(url).func.view_class == EmailVerify

    def test_ConfirmEmailView(self):
        url = reverse('confirm_email')
        assert resolve(url).func.view_class == ConfirmEmailView

    def test_InvalidVerifyView(self):
        url = reverse('invalid_verify')
        assert resolve(url).func.view_class == InvalidVerifyView

    def test_LogoutView(self):
        url = reverse('logout')
        assert resolve(url).func == logout_user
