import shutil
import tempfile
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class TestPostsViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group_with_posts = Group.objects.create(
            title="Группа с постами",
            slug="test_slug",
            description="Описание группы с постами для теста views",
        )

        cls.group_without_posts = Group.objects.create(
            title="Группа без постов",
            slug="test_slug_no_posts",
            description="Описание группы без постов для теста views",
        )

        cls.author = User.objects.create_user(username="test_dummy_author")

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.marker_post = Post.objects.create(
            pk=0,
            text="Marker post",
            author=cls.author,
            group=cls.group_with_posts,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_use_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = (
            ("posts/index.html", reverse("posts:index")),
            ("posts/new_post.html", reverse("posts:new_post")),
            ("posts/group.html", reverse(
                "posts:group",
                kwargs={"slug": "test_slug"}
            )),
        )

        for template, reverse_name in templates_page_names:
            with self.subTest(template=template, reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                self.assertTemplateUsed(response, template)

    def test_pages_with_pagination_have_correct_context(self):
        """На страницы с паджинатором выводится правильный
        контекст для отображения поста."""
        pages = (
            reverse("posts:index"),
            reverse(
                "posts:group",
                kwargs={"slug": self.group_with_posts.slug}
            ),
            reverse(
                "posts:profile",
                kwargs={"username": self.author.username}
            ),
        )

        for page in pages:
            response = self.authorized_client.get(page)
            instance_from_page = response.context["page"].object_list[0]
            with self.subTest(page=page):
                self.assertEqual(
                    instance_from_page.text,
                    self.marker_post.text
                )
                self.assertEqual(
                    instance_from_page.author,
                    self.marker_post.author
                )
                self.assertEqual(
                    instance_from_page.image,
                    self.marker_post.image
                )

    def test_group_page_has_correct_group_data_context(self):
        """На страницу группы выводится правильная информация о группе."""
        page = reverse("posts:group", kwargs={"slug": "test_slug"})

        response = self.authorized_client.get(page)
        group = response.context["group"]

        self.assertEqual(
            group.slug,
            self.group_with_posts.slug
        )
        self.assertEqual(
            group.description,
            self.group_with_posts.description
        )
        self.assertEqual(
            group.title,
            self.group_with_posts.title
        )

    def test_profile_page_has_correct_user_data_context(self):
        """На страницу профиля выводится правильная
        информация о пользователе."""
        page = reverse(
            "posts:profile",
            kwargs={"username": "test_dummy_author"}
        )

        response = self.authorized_client.get(page)
        author = response.context["profile_data"]

        self.assertEqual(author.username, self.author.username)

    def test_paginator_pages_have_expected_object_list(self):
        """На страницах с паджинатором выводятся ожидаемые посты
        в ожидаемом порядке и количестве."""
        Post.objects.bulk_create(
            [
                Post(
                    text=f"Test post {post_num}",
                    author=self.author,
                    group=self.group_with_posts,
                )
                for post_num in range(12)
            ]
        )
        urls = (
            (
                reverse("posts:index"),
                Post.objects.all().order_by("-pub_date")
            ),
            (
                reverse("posts:group", kwargs={"slug": "test_slug"}),
                Post.objects.filter(
                    group=self.group_with_posts
                ).order_by("-pub_date")
            ),
            (
                reverse(
                    "posts:profile",
                    kwargs={"username": self.author.username}
                ),
                Post.objects.filter(
                    author=self.author
                ).order_by("-pub_date")
            ),
        )

        for url, db_posts in urls:
            pages = (
                (1, db_posts[:10]),
                (2, db_posts[10:])
            )
            for page_num, expected_posts in pages:
                with self.subTest(url=url, page_num=page_num):
                    response = self.authorized_client.get(
                        f"{url}?page={page_num}"
                    )
                    page_obj_list = response.context["page"].object_list

                    self.assertEqual(len(page_obj_list), len(expected_posts))
                    self.assertEqual(list(page_obj_list), list(expected_posts))

    def test_new_post_page_has_correct_context(self):
        """На страницу создания поста выводится правильный контекст."""
        page = reverse("posts:new_post")

        response = self.authorized_client.get(page)

        self.assertIsInstance(response.context["form"], PostForm)

    def test_edit_post_page_has_correct_context(self):
        """На страницу редактирования поста выводится правильный контекст."""
        page = reverse(
            "posts:edit_post",
            kwargs={
                "username": self.author.username,
                "post_id": self.marker_post.pk
            },
        )

        response = self.authorized_client.get(page)

        self.assertEqual(response.context["username"], self.author.username)
        self.assertIsInstance(response.context["form"], PostForm)

    def test_post_page_has_correct_context(self):
        """На страницу поста выводится правильный контекст."""
        page = reverse(
            "posts:post",
            kwargs={
                "username": self.marker_post.author.username,
                "post_id": self.marker_post.pk
            }
        )
        expected_context = {
            "post": self.marker_post,
            "author": self.marker_post.author,
        }

        response = self.authorized_client.get(page)
        for value, expected_value in expected_context.items():
            with self.subTest(value=value, expected_value=expected_value):
                self.assertEqual(response.context[value], expected_value)
        self.assertEqual(response.context["post"].image, "posts/small.gif")

    def test_new_post_page_has_correct_form(self):
        """На страницу выводится правильная форма."""
        page = reverse("posts:new_post")

        response = self.authorized_client.get(page)
        form = response.context["form"]

        self.assertEqual(form.initial, {})

    def test_edit_post_page_has_correct_form(self):
        """На страницу выводится правильная форма."""
        page = reverse(
            "posts:edit_post",
            kwargs={
                "username": self.marker_post.author,
                "post_id": self.marker_post.pk,
            },
        )
        form_fields = (
            ("group", self.marker_post.group.pk),
            ("text", self.marker_post.text),
        )

        response = self.authorized_client.get(page)
        form = response.context["form"]
        for value, expected_value in form_fields:
            with self.subTest(value=value, expected_value=expected_value):
                self.assertEqual(form.initial[value], expected_value)

    def test_index_page_caching(self):
        """Посты на главной странице кэшируются."""
        self.authorized_client.get(reverse("posts:index"))
        post = Post.objects.create(
            text="Пост для тестирования кэша",
            author=self.author,
        )

        response_1 = self.authorized_client.get(reverse("posts:index"))
        cache.clear()
        response_2 = self.authorized_client.get(reverse("posts:index"))

        self.assertNotContains(
            response_1,
            post.text
        )
        self.assertTemplateNotUsed(response_1, "posts/post_handler.html")
        self.assertContains(
            response_2,
            post.text
        )
        self.assertTemplateUsed(response_2, "posts/post_handler.html")

    def test_posts_exist_on_expected_pages(self):
        """Посты появляются там, где должны."""
        index = reverse("posts:index")
        group_with_posts = reverse(
            "posts:group",
            kwargs={"slug": self.group_with_posts.slug}
        )
        created_post = Post.objects.create(
            text="Созданный пост",
            author=self.author,
        )
        created_post_with_group = Post.objects.create(
            text="Созданный пост",
            group=self.group_with_posts,
            author=self.author,
        )
        expected_locations = (
            (
                created_post,
                (index,),
            ),
            (
                created_post_with_group,
                (index, group_with_posts),
            )
        )

        for post, in_pages in expected_locations:
            for page in in_pages:
                with self.subTest(page=page):
                    response = self.authorized_client.get(index)

                    self.assertIn(
                        post,
                        response.context["page"].object_list
                    )

    def test_posts_does_not_exist_on_unexpected_pages(self):
        """Посты не появляются там, где не должны."""
        group_with_posts = reverse(
            "posts:group",
            kwargs={"slug": self.group_with_posts.slug}
        )
        group_without_posts = reverse(
            "posts:group",
            kwargs={"slug": self.group_without_posts.slug}
        )
        created_post = Post.objects.create(
            text="Созданный пост",
            author=self.author,
        )
        created_post_with_group = Post.objects.create(
            text="Созданный пост",
            group=self.group_with_posts,
            author=self.author,
        )
        expected_locations = (
            (
                created_post,
                (group_with_posts, group_without_posts),
            ),
            (
                created_post_with_group,
                (group_without_posts,),
            )
        )

        for post, not_in_pages in expected_locations:
            for page in not_in_pages:
                with self.subTest(page=page):
                    response = self.authorized_client.get(page)

                    self.assertNotIn(
                        post,
                        response.context["page"].object_list
                    )

    def test_subscription(self):
        """Авторизованый пользователь может подписываться/отписываться
         на/от других пользователей"""
        follower = User.objects.create_user(username="test_dummy_follower")
        follower_client = Client()
        follower_client.force_login(follower)
        page_follow = reverse(
            "posts:profile_follow",
            kwargs={"username": self.author}
        )
        page_unfollow = reverse(
            "posts:profile_unfollow",
            kwargs={"username": self.author}
        )

        follower_client.post(page_follow)
        follow_response = Follow.objects.filter(
            user=follower,
            author=self.author
        ).exists()
        follower_client.post(page_unfollow)
        unfollow_response = Follow.objects.filter(
            user=follower,
            author=self.author
        ).exists()

        self.assertTrue(follow_response)
        self.assertFalse(unfollow_response)

    def test_posts_appears_only_on_followers_follow_index_page(self):
        """На странице подписок посты появляются только у подписчиков."""
        follower = User.objects.create_user(
            username="test_dummy_follower"
        )
        follower_client = Client()
        follower_client.force_login(follower)
        not_follower = User.objects.create_user(
            username="test_dummy_not_follower"
        )
        not_follower_client = Client()
        not_follower_client.force_login(not_follower)
        Follow.objects.create(user=follower, author=self.author)

        follower_response = follower_client.get(
            reverse("posts:follow_index")
        )
        not_follower_response = not_follower_client.get(
            reverse("posts:follow_index")
        )

        self.assertIn(
            self.marker_post,
            follower_response.context["page"]
        )
        self.assertNotIn(
            self.marker_post,
            not_follower_response.context["page"]
        )

    def test_only_authorized_users_can_leave_comments(self):
        """Только авторизованные пользователи могут оставлять комментарии."""
        page = reverse(
            "posts:add_comment",
            kwargs={
                "username": self.author.username,
                "post_id": self.marker_post.pk,
            }
        )
        unauthorised_client = Client()
        clients_comments = (
            (self.authorized_client, "Authorised comment"),
            (unauthorised_client, "Unauthorised comment"),
        )

        for client, comment in clients_comments:
            form_data = {"text": comment, }
            client.post(page, data=form_data)

        self.assertTrue(
            Comment.objects.filter(text="Authorised comment").exists()
        )
        self.assertFalse(
            Comment.objects.filter(text="Unauthorised comment").exists()
        )
