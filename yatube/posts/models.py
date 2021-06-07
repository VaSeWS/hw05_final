from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
    )
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        help_text="Текст поста не может быть пустым",
        verbose_name="Текст поста"
    )
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        help_text="В какой группе выложить пост",
        verbose_name="Группа (необязательно)"
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True,
        help_text="Загрузите картинку",
        verbose_name="Изображение (необязательно)"
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ("-pub_date",)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField()
    created = models.DateTimeField(
        "date published",
        auto_now_add=True
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following"
    )
