from django.test import LiveServerTestCase, Client
from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_driver import get_driver

User = get_user_model()

class SaqTests(LiveServerTestCase):

    def setUp(self):
        self.driver = get_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.user = User.objects.create_superuser(
            username="test_user",
            password="test1234",
            email="test@test.com"
        )
        # Login forzado sin reCAPTCHA
        client = Client()
        client.force_login(self.user)
        cookie = client.cookies['sessionid']
        self.driver.get(f"{self.live_server_url}/")
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'path': '/',
        })

    def tearDown(self):
        self.driver.quit()

    def test_pagina_saq_carga(self):
        self.driver.get(f"{self.live_server_url}/saq/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}/saq/")

    def test_formulario_saq_visible(self):
        self.driver.get(f"{self.live_server_url}/saq/")
        formulario = self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        self.assertTrue(formulario.is_displayed())

    def test_responder_pregunta(self):
        self.driver.get(f"{self.live_server_url}/saq/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # Verifica que la página cargó correctamente
        self.assertIn("saq", self.driver.current_url)