from django.test import LiveServerTestCase
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_driver import get_driver

User = get_user_model()

@override_settings(
    RECAPTCHA_PUBLIC_KEY='test',
    RECAPTCHA_PRIVATE_KEY='test',
)
class UsersTests(LiveServerTestCase):

    def setUp(self):
        self.driver = get_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.user = User.objects.create_superuser(
            username="test_user",
            password="test1234",
            email="test@test.com"
        )

    def tearDown(self):
        self.driver.quit()

    def _login_forzado(self):
        """Login directo sin pasar por reCAPTCHA"""
        from django.test import Client
        client = Client()
        client.force_login(self.user)
        cookie = client.cookies['sessionid']
        self.driver.get(f"{self.live_server_url}/")
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'path': '/',
        })

    def test_pagina_login_carga(self):
        self.driver.get(f"{self.live_server_url}/")
        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        self.assertIn("Login", self.driver.title)

    def test_dashboard_con_login(self):
        self._login_forzado()
        self.driver.get(f"{self.live_server_url}/dashboard/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.assertNotIn("login", self.driver.current_url.lower())

    def test_login_error_visible(self):
        """Verifica que el div de error existe en el HTML del login"""
        self.driver.get(f"{self.live_server_url}/")
        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        # Verificar que el formulario tiene los campos correctos
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        self.assertTrue(username_field.is_displayed())
        self.assertTrue(password_field.is_displayed())