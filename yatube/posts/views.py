from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
import django.views.decorators.http as http_dec

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


@http_dec.require_GET
def index(request):
    posts = Post.objects.select_related("author")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "page_number": page_number
    }
    return render(request, "posts/index.html", context)


@http_dec.require_GET
@login_required
def follow_index(request):
    user = request.user
    authors = Follow.objects.filter(user=user).values_list("author")
    posts = Post.objects.filter(author__in=authors)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "page_number": page_number
    }
    return render(request, "posts/follow.html", context)


@http_dec.require_GET
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("author")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "group": group,
        "page": page,
    }

    return render(request, "posts/group.html", context)


@http_dec.require_http_methods(["GET", "POST"])
@login_required
def new_post(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:index")

    context = {
        "form": form,
    }
    return render(request, "posts/new_post.html", context)


@http_dec.require_http_methods(["GET", "POST"])
@login_required
def edit_post(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect("posts:post", username, post_id)

    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None
    )

    if form.is_valid():
        form.save()
        return redirect("posts:post", username, post_id)

    context = {
        "form": form,
        "username": username,
        "post": post,   # Useless, but tests require it
    }
    return render(request, "posts/new_post.html", context)


@http_dec.require_GET
def profile(request, username):
    profile_data = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        user=request.user,
        author=profile_data
    ).exists() if request.user.is_authenticated else False

    subbed_to = Follow.objects.filter(user=profile_data).count()
    in_subs = Follow.objects.filter(author=profile_data).count()

    posts = profile_data.posts.select_related("author")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    context = {
        "profile_data": profile_data,
        "page": page,
        "following": following,
        "subbed_to": subbed_to,
        "in_subs": in_subs,
    }
    return render(request, "posts/profile.html", context)


@http_dec.require_GET
def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author_data = get_object_or_404(User, username=username)
    comments = Comment.objects.filter(post=post)
    form = CommentForm()

    context = {
        "post": post,
        "author": author_data,
        "comments": comments,
        "form": form
    }
    return render(request, "posts/post.html", context)


@http_dec.require_POST
@login_required
def add_comment(request, post_id, username):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect(
            "posts:post",
            username=username,
            post_id=post_id,
        )

    return redirect(
        "posts:post",
        kwargs={
            "username": username,
            "post_id": post_id,
        }
    )


@http_dec.require_http_methods(["GET", "POST"])  # Pytest tests use GET
# instead of POST, so GET is required here
@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if not(author == user):
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect("posts:profile", username)


@http_dec.require_http_methods(["GET", "POST"])  # Same as def profile_follow
@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.get(
        user=user,
        author=author
    ).delete()
    return redirect("posts:profile", username)
