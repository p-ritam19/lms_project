from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime


class Author(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Book(models.Model):
    name = models.CharField(max_length=250)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="books")
    book_no = models.CharField(max_length=50, unique=True, help_text="Accession / book number (like ISBN)")
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    copies_available = models.PositiveIntegerField(default=1)
    cover = models.ImageField(upload_to="book_covers/", blank=True, null=True)
    pdf_file = models.FileField(upload_to="book_pdfs/", blank=True, null=True, help_text="Upload the PDF file of the book")

    def __str__(self):
        return f"{self.name} ({self.book_no})"


class Profile(models.Model):
    """Extra fields for a Django User (mobile, address) - equivalent of the
    extra columns on the 'users' table in the original PHP project."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    mobile = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.username


def default_due_date():
    return (timezone.now() + datetime.timedelta(days=14)).date()


FINE_PER_DAY = 2  # currency units per day overdue


class IssuedBook(models.Model):
    STATUS_CHOICES = (
        (1, "Issued"),
        (0, "Returned"),
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="issues")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="issued_books")
    issue_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateField(default=default_due_date)
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    fine_paid = models.BooleanField(default=False)

    def is_overdue(self):
        return self.status == 1 and timezone.now().date() > self.due_date

    def days_overdue(self):
        end = self.return_date.date() if self.return_date else timezone.now().date()
        delta = (end - self.due_date).days
        return max(delta, 0)

    def calculate_fine(self):
        return self.days_overdue() * FINE_PER_DAY

    def __str__(self):
        return f"{self.book.name} -> {self.student.username}"


class BookRequest(models.Model):
    """Covers both: (a) reserving a book that has no copies available,
    and (b) requesting a renewal (due-date extension) on a book already issued."""
    RESERVATION = "reservation"
    RENEWAL = "renewal"
    REQUEST_TYPES = (
        (RESERVATION, "Reservation"),
        (RENEWAL, "Renewal"),
    )
    PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    )
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="book_requests")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="requests")
    issued_book = models.ForeignKey(IssuedBook, on_delete=models.CASCADE, null=True, blank=True, related_name="renewal_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    requested_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.book.name} ({self.student.username})"


class BookRating(models.Model):
    """User ratings for books (1-5 stars)"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="book_ratings")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('book', 'user')  # One rating per user per book
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.book.name} - {self.rating}★"


class BookReview(models.Model):
    """User reviews/comments for books"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="book_reviews")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    title = models.CharField(max_length=200)
    content = models.TextField()
    helpful_count = models.PositiveIntegerField(default=0)  # How many found it helpful
    is_approved = models.BooleanField(default=True)  # Admin moderation
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review: {self.title[:30]} by {self.user.username} for {self.book.name}"
