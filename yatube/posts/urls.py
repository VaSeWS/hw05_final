from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path(
        "",
        views.index,
        name="index"
    ),
    path(
        "new/",
        views.new_post,
        name="new_post"
    ),
    path(
        "group/<slug:slug>/",
        views.group_posts,
        name="group"
    ),
    path(
        "follow/",
        views.follow_index,
        name="follow_index"
    ),
    path(
        "<str:username>/",
        views.profile,
        name="profile"
    ),
    path(
        "<str:username>/<int:post_id>/",
        views.post_view,
        name="post"
    ),
    path(
        "<str:username>/<int:post_id>/edit/",
        views.edit_post,
        name="edit_post"
    ),
    path(
        "<username>/<int:post_id>/comment/",
        views.add_comment,
        name="add_comment"
    ),
    path(
        "<str:username>/follow/",
        views.profile_follow,
        name="profile_follow"
    ),
    path(
        "<str:username>/unfollow/",
        views.profile_unfollow,
        name="profile_unfollow"
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )