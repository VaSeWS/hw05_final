from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class TestAboutViews(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_accessible_by_name(self):
        """URL, генерируемые при помощи имен about:author и about:tech,
        доступны."""
        urls = (
            reverse("about:author"),
            reverse("about:tech"),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_pages_uses_correct_template(self):
        """При запросе к about:author и about:tech применяются правильные
        шаблоны."""
        urls = (
            (reverse("about:author"), "about/author.html"),
            (reverse("about:tech"), "about/tech.html"),
        )
        for url, template in urls:
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
