from rest_framework.permissions import BasePermission


class IsAuthor(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == "author"
        )


class IsReader(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == "reader"
        )


class IsAuthorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ["GET"]:
            return True
        return bool(
            request.user and request.user.is_authenticated and request.user.role == "author"
        )
