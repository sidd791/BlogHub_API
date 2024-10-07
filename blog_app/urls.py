from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    RegisterView,
    author_list,
    author_view,
    reader_list,
    reader_view,
    tag_list,
    tag_view,
    post_create,
    post_view,
    post_list,
    comment_list_create,
    comment_view,
    like_post,
    unlike_post,
    get_likes,
    follow_author,
    get_author_followers,
    unfollow_author,
    PasswordResetView,
    password_reset_confirm
)


urlpatterns = [
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('api/password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('api/password_reset/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),

    # User Registration
    path("api/register/", RegisterView.as_view(), name="register"),

    # Author URLs
    path("api/authors/", author_list, name="author_list"),
    path("api/authors/<int:pk>/", author_view, name="author_detail"),

    # Reader URLs
    path("api/readers/", reader_list, name="reader_list"),
    path("api/readers/<int:pk>/", reader_view, name="reader_detail"),

    # Tag URLs
    path("api/tags/", tag_list, name="tag_list"),
    path("api/tags/<int:pk>/", tag_view, name="tag_detail"),

    # Post URLs
    path("api/posts/", post_list, name="post_list"),
    path("api/posts/create/", post_create, name="post_create"),
    path("api/posts/<int:pk>/", post_view, name="post_detail"),

    # Comment URLs
    path("api/posts/<int:post_pk>/comments", comment_list_create, name="comment_list_create"),
    path("api/posts/<int:post_pk>/comments/<int:comment_pk>/", comment_view, name="comment_detail"),

    # Like URLs
    path("api/posts/like/<int:post_id>/", like_post, name="like_post"),
    path("api/posts/unlike/<int:post_id>/", unlike_post, name="unlike_post"),
    path("api/posts/likes/<int:post_id>/", get_likes, name="get_likes"),

    # Follow URLs
    path('authors/follow/<int:author_id>/', follow_author, name='follow_author'),
    path('authors/unfollow/<int:author_id>/', unfollow_author, name='unfollow_author'),
    path('authors/followers/<int:author_id>/', get_author_followers, name='get_author_followers'),
]
