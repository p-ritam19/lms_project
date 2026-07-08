from rest_framework import serializers
from .models import Author, Category, Book, IssuedBook


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class BookSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Book
        fields = [
            "id", "name", "author", "author_name", "category", "category_name",
            "book_no", "price", "copies_available", "cover",
        ]


class IssuedBookSerializer(serializers.ModelSerializer):
    book_name = serializers.CharField(source="book.name", read_only=True)
    student_name = serializers.CharField(source="student.username", read_only=True)
    fine = serializers.SerializerMethodField()

    class Meta:
        model = IssuedBook
        fields = [
            "id", "book", "book_name", "student", "student_name",
            "issue_date", "due_date", "return_date", "status", "fine",
        ]

    def get_fine(self, obj):
        return obj.calculate_fine()
