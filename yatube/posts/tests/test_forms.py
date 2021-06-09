import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class TestPostsForms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test_dummy_author")
        cls.group = Group.objects.create(
            title="Тестовый Заголовок",
            slug="test_header",
            description="Описание группы для теста формы",
        )
        cls.another_group = Group.objects.create(
            title="Тестовый Заголовок 2",
            slug="another_test_header",
            description="Описание группы для теста изменения группы поста",
        )
        cls.edit_test_post = Post.objects.create(
            text="Этот пост будет использован для проверки "
            "работы страницы редактирования поста",
            author=cls.user,
            group=cls.group,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)

    def test_post_creation(self):
        """Валидная форма создает запись Post."""

        form_pieces_of_data = (
            {
                "text": "Этот пост будет создан через форму создания поста",
                "group": self.group.pk,
            },
            {
                "text": "Этот пост будет создан через форму создания поста",
                "image": self.uploaded,
            },
        )

        for form_data in form_pieces_of_data:
            with self.subTest(form_data=form_data):
                posts_count = Post.objects.count()
                response = self.authorised_client.post(
                    path=reverse("posts:new_post"),
                    data=form_data,
                    follow=True
                )

                self.assertRedirects(
                    response,
                    reverse("posts:index"),
                )
                self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Этот пост будет создан через форму "
                     "создания поста",
                author=self.user,
                group=form_data.get("group"),
            ).exists()
        )
        self.assertTrue(
            Post.objects.filter(
                text="Этот пост будет создан через форму "
                     "создания поста",
                author=self.user,
                image__icontains="posts/small"
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма изменяет пост."""

        posts_count = Post.objects.count()
        form_data = {
            "text": "Этот пост был использован для проверки работы "
            "страницы редактирования поста с группой",
            "group": self.another_group.pk,
            "image": self.uploaded
        }

        response = self.authorised_client.post(
            path=reverse(
                "posts:edit_post",
                kwargs={
                    "username": self.edit_test_post.author,
                    "post_id": self.edit_test_post.pk
                },
            ),
            data=form_data,
            follow=True,
        )

        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response,
            reverse(
                "posts:post",
                kwargs={
                    "username": self.edit_test_post.author,
                    "post_id": self.edit_test_post.pk
                },
            ),
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                author=self.user,
                group=form_data.get("group"),
                image__icontains="posts/small"
            ).exists()
        )

    def test_invalid_form(self):
        """Некорректная форма не создает/не редактирует пост."""
        posts_count = Post.objects.count()
        post = self.edit_test_post
        not_existing_group_id = -1
        form_pieces_of_data = (
            {
                "text": ""
            },
            {
                "text": "Этот не должно попасть в БД",
                "group": not_existing_group_id
            },
        )
        urls = (
            (reverse("posts:new_post"), HTTPStatus.OK),
            (
                reverse(
                    "posts:edit_post",
                    kwargs={"username": post.author, "post_id": post.pk},
                ),
                HTTPStatus.OK,
            ),
        )

        for url, request_code in urls:
            for form_data in form_pieces_of_data:
                with self.subTest(
                    url=url, request_code=request_code, form_data=form_data
                ):
                    response = self.authorised_client.post(
                        path=url, data=form_data, follow=True
                    )

                    self.assertEqual(Post.objects.count(), posts_count)
                    self.assertEqual(response.status_code, request_code)
