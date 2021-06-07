from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class TestGroupModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = Group.objects.create(
            title="Тестовый Заголовок",
            slug="test_header",
            description="Описание группы для теста модели",
        )

    def test_object_name(self):
        """group.__str__ равна значению поля group.title."""
        group = self.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))


class TestPostModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
            username="test_user",
        )
        cls.post = Post.objects.create(
            text="Текст тестового поста.",
            author=user,
        )

    def test_object_name(self):
        """post.__str__ равна значению post.text[:15]."""
        post = self.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_fields_verboses(self):
        """Поля имеют правильное значение параметра verbose_name."""
        expected_values = (
            ("text", "Текст поста"),
            ("group", "Группа (необязательно)")
        )
        for field, expected_verbose in expected_values:
            with self.subTest(field=field, expected_verbose=expected_verbose):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name, expected_verbose
                )

    def test_fields_help_text(self):
        """Поля имеют правильное значение параметра help_text."""
        expected_values = (
            ("text", "Текст поста не может быть пустым"),
            ("group", "В какой группе выложить пост"),
        )
        for field, expected_help_field in expected_values:
            with self.subTest(
                    field=field,
                    expected_help_field=expected_help_field
            ):

                self.assertEqual(
                    Post._meta.get_field(field).help_text, expected_help_field
                )
