from rest_framework import status
from rest_framework.response import Response
from .permissions import IsAuthor, IsReader, IsAuthorOrReadOnly
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import *
from rest_framework.decorators import api_view, permission_classes
from .serializers import (
    UserSerializer,
    AuthorSerializer,
    ReaderSerializer,
    TagSerializer,
    PostSerializer,
    LikeSerializer,
    CommentSerializer,
    FollowSerializer
)
from rest_framework.generics import CreateAPIView
from django.db.models import Q
from .tasks import notify_author_of_new_comment, notify_readers_of_new_post
from rest_framework.pagination import PageNumberPagination


class RegisterView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


# Author Views
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAuthor])
def author_list(request):
    authors = Author.objects.all()
    serializer = AuthorSerializer(authors, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAuthor])
def author_view(request, pk):
    try:
        author = Author.objects.get(pk=pk)
        if author.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
    except Author.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        serializer = AuthorSerializer(author)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == "PUT":
        serializer = AuthorSerializer(author, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    elif request.method == "DELETE":
        author.delete()
        return Response(status=status.HTTP_200_OK)


# Reader views
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsReader])
def reader_list(request):
    readers = Reader.objects.all()
    serializer = ReaderSerializer(readers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsReader])
def reader_view(request, pk):
    try:
        reader = Reader.objects.get(pk=pk)
        if reader.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
    except Reader.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        serializer = ReaderSerializer(reader)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = ReaderSerializer(reader, data=request.data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors)
    elif request.method == "DELETE":
        reader.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Tag Views
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def tag_list(request):
    if request.method == "GET":
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == "POST":
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "DELETE", "PUT"])
@permission_classes([IsAuthenticated])
def tag_view(request, pk):
    try:
        tag = Tag.objects.get(pk=pk)
    except Tag.DoesNotExist:
        return Response(status=status.HTTP_200_OK)
    if request.method == "GET":
        serializer = TagSerializer(tag)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == "PUT":
        serializer = TagSerializer(tag, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    elif request.method == "DELETE":
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Post Views
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAuthorOrReadOnly])
def post_view(request, pk):
    try:
        post = Post.objects.get(pk=pk)

        # Restrict access to drafts for non-authors
        if post.status == 'draft' and post.author.user != request.user:
            return Response({"detail": "You do not have permission to view this draft."},
                            status=status.HTTP_403_FORBIDDEN)

    except Post.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "PUT":
        if post.author.user != request.user:
            return Response({"detail": "You do not have permission to edit this post."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        if post.author.user != request.user:
            return Response({"detail": "You do not have permission to delete this post."},
                            status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAuthor])
def post_create(request):
    if request.method == "POST":
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user.author)
            notify_readers_of_new_post.delay(request.user.id, request.data.content)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def post_list(request):
    if request.user.role == "author":
        # Authors see all their own posts, including drafts
        posts = Post.objects.filter(author=request.user.author)
    else:
        # Readers see only published posts
        posts = Post.objects.filter(status='published')

    # Filtering by tags
    tag_names = request.query_params.getlist('tags', None)
    if tag_names:
        posts = posts.filter(tags__id__in=tag_names).distinct()

    # Filtering by published dates
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)

    if start_date:
        posts = posts.filter(created_at__gte=start_date)

    if end_date:
        posts = posts.filter(created_at__lte=end_date)

    # Search functionality
    search_query = request.query_params.get('search', None)
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()

    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginated_posts = paginator.paginate_queryset(posts, request)
    serializer = PostSerializer(paginated_posts, many=True)
    return paginator.get_paginated_response(serializer.data)


#Comment Views
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def comment_list_create(request, post_pk):
    try:
        post = Post.objects.get(pk=post_pk)
    except Post.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        comments = Comment.objects.filter(post=post)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(user=request.user, post=post)
            notify_author_of_new_comment.delay(post.id, comment.content)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def comment_view(request, post_pk, comment_pk):
    try:
        comment = Comment.objects.get(pk=comment_pk, post__pk=post_pk)
    except Comment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "PUT":
        if comment.user != request.user:
            return Response({"error": "You are not allowed to edit this comment"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        if comment.user != request.user:
            return Response({"error": "You are not allowed to delete this comment"}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

#Like Views
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def like_post(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if the post is already liked by the user
    if Like.objects.filter(post=post, user=request.user).exists():
        return Response({"detail": "You have already liked this post"}, status=status.HTTP_400_BAD_REQUEST)

    like = Like(post=post, user=request.user)
    like.save()

    return Response({"detail": "Post liked successfully"}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unlike_post(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        like = Like.objects.get(post=post, user=request.user)
        like.delete()
        return Response({"detail": "Post unliked successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Like.DoesNotExist:
        return Response({"detail": "You have not liked this post"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_likes(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    likes = Like.objects.filter(post=post)
    serializer = LikeSerializer(likes, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Follow Views
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def follow_author(request, author_id):
    try:
        reader = Reader.objects.get(user=request.user)
        author = Author.objects.get(id=author_id)
    except Reader.DoesNotExist:
        return Response({"detail": "Reader profile not found."}, status=status.HTTP_404_NOT_FOUND)
    except Author.DoesNotExist:
        return Response({"detail": "Author not found."}, status=status.HTTP_404_NOT_FOUND)

    data = {'reader': reader.id, 'author': author.id}
    serializer = FollowSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unfollow_author(request, author_id):
    try:
        reader = Reader.objects.get(user=request.user)
        author = Author.objects.get(id=author_id)
        follow = Follow.objects.get(reader=reader, author=author)
    except (Reader.DoesNotExist, Author.DoesNotExist, Follow.DoesNotExist):
        return Response({"detail": "Follow relationship not found."}, status=status.HTTP_404_NOT_FOUND)

    follow.delete()
    return Response({"detail": "Unfollowed successfully."}, status=status.HTTP_204_NO_CONTENT)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_author_followers(request, author_id):
    try:
        author = Author.objects.get(id=author_id)
    except Author.DoesNotExist:
        return Response({"detail": "Author not found."}, status=status.HTTP_404_NOT_FOUND)

    followers = Follow.objects.filter(author=author)
    serializer = FollowSerializer(followers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.dispatch import receiver
from rest_framework import generics
from .signals import password_reset_requested
from .tasks import send_password_reset_email

class PasswordResetView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            # Trigger the password reset signal
            password_reset_requested.send(sender=self.__class__, user=user)
            return Response({"detail": "Password reset email sent."}, status=status.HTTP_200_OK)
        return Response({"detail": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

@receiver(password_reset_requested)
def password_reset_email(sender, user, **kwargs):
    subject = "Password Reset Requested"
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    url = f"http://localhost:8000/api/password_reset/{uid}/{token}/"
    message = render_to_string('password_reset_email.html', {'url': url, 'user': user})
    send_password_reset_email.delay(subject, message ,user.email)


@api_view(["POST"])
def password_reset_confirm(request, uidb64, token):
    try:
        # Decode the uid to get the user ID
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid token or user ID."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the token is valid
    if not default_token_generator.check_token(user, token):
        return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

    # Get the new password from the request data
    new_password = request.data.get("new_password", None)

    if new_password:
        # Set the new password
        user.set_password(new_password)
        user.save()
        return Response({"success": "Password has been reset."}, status=status.HTTP_200_OK)

    return Response({"error": "New password not provided."}, status=status.HTTP_400_BAD_REQUEST)