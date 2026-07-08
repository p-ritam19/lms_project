from rest_framework import viewsets, permissions
from .models import Author, Category, Book, IssuedBook
from .serializers import AuthorSerializer, CategorySerializer, BookSerializer, IssuedBookSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all().order_by("name")
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related("author", "category").all().order_by("name")
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["author", "category"]


class IssuedBookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IssuedBook.objects.select_related("book", "student").all().order_by("-issue_date")
    serializer_class = IssuedBookSerializer
    permission_classes = [permissions.IsAdminUser]
