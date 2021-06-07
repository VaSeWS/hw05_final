from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class TestPostsURL(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = Group.objects.create(
            title="Тестовый Заголовок",
            slug="test_slug",
            description="Описание группы для теста модели",
        )

        cls.author = User.objects.create_user(username="test_dummy_author")

        cls.post = Post.objects.create(
            text="Текст тестового поста.",
            author=cls.author,
            group=cls.group,
        )

        cls.user = User.objects.create_user(username="test_dummy")

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_response_code_guest(self):
        """Страница доступна неавторизованному пользователю."""
        urls = (
            ("/", HTTPStatus.OK),
            ("/new/", HTTPStatus.FOUND),
            ("/group/test_slug/", HTTPStatus.OK),
            ("/test_dummy_author/", HTTPStatus.OK),
            ("/test_dummy_author/1/", HTTPStatus.OK),
        )

        for url, response_code in urls:
            with self.subTest(url=url, response_code=response_code):
                response = self.guest_client.get(url)

                self.assertEqual(response.status_code, response_code)

    def test_response_code_authorised(self):
        """Страница доступна авторизованному пользователю."""
        urls = (
            "/",
            "/new/",
            "/group/test_slug/",
            "/test_dummy_author/",
            "/test_dummy_author/1/",
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            ("/", "posts/index.html"),
            ("/new/", "posts/new_post.html"),
            ("/group/test_slug/", "posts/group.html"),
            ("/test_dummy_author/1/edit/", "posts/new_post.html"),
        )

        for url, template in templates_url_names:
            with self.subTest(url=url, template=template):
                response = self.authorized_client_author.get(url)

                self.assertTemplateUsed(response, template)

    def test_response_code_post_edit_page(self):
        """К странице изменения поста имеет доступ только автор."""

        users = (
            (self.guest_client, HTTPStatus.FOUND),
            (self.authorized_client, HTTPStatus.FOUND),
            (self.authorized_client_author, HTTPStatus.OK),
        )

        for user, response_code in users:
            with self.subTest(user=user, response_code=response_code):
                response = user.get("/test_dummy_author/1/edit/")

                self.assertEqual(response.status_code, response_code)

    def test_post_edit_redirect(self):
        """Со страницы редактирования поста ведут правильные редиректы."""
        users = (
            (
                self.guest_client,
                "/auth/login/?next=/test_dummy_author/1/edit/"
            ),
            (self.authorized_client, "/test_dummy_author/1/"),
        )

        for user, redirect_url in users:
            with self.subTest(user=user, redirect_url=redirect_url):
                response = user.get("/test_dummy_author/1/edit/")

                self.assertRedirects(response, redirect_url)

    def test_404_page(self):
        """При переходе на несуществующую ссылку сервер возвращает код 404"""
        response = self.authorized_client.get(
            "/is_there_life_on_mars/?david=bowie"
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
