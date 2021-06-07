from http import HTTPStatus

from django.test import Client, TestCase


class TestAboutUrls(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_exists_at_desired_location(self):
        """Проверка доступности адрессов приложения about."""
        urls = ("/about/author/", "/about/tech/")
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_pages_uses_correct_template(self):
        """Проверка шаблонов для адрессов приложения about."""
        urls = (
            ("/about/author/", "about/author.html"),
            ("/about/tech/", "about/tech.html"),
        )
        for url, template in urls:
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
