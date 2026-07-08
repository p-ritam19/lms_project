import io
import json
import qrcode
import secrets
import base64
from collections import Counter

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.urls import reverse

from .models import Author, Category, Book, Profile, IssuedBook, BookRequest, FINE_PER_DAY, BookRating, BookReview
from .forms import (
    SignupForm, LoginForm, ProfileEditForm, ChangePasswordForm,
    AuthorForm, CategoryForm, BookForm, IssueBookForm, ForgotPasswordForm, ResetPasswordForm,
    BookRatingForm, BookReviewForm,
)


def is_admin(user):
    return user.is_authenticated and user.is_staff


def notify(subject, message, to_email):
    """Best-effort email notification. Uses the console backend in dev,
    so nothing breaks if there's no real mail server configured."""
    if not to_email:
        return
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=True)
    except Exception:
        pass


# ---------- Public pages ----------

def index(request):
    """User login / landing page."""
    if request.user.is_authenticated:
        return redirect("user_dashboard")
    form = LoginForm()
    error = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            try:
                username = User.objects.get(email=email, is_staff=False).username
            except User.DoesNotExist:
                username = None
            user = authenticate(request, username=username, password=password) if username else None
            if user:
                login(request, user)
                return redirect("user_dashboard")
            error = "Wrong email or password!"
    return render(request, "library/index.html", {"form": form, "error": error})


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard")
    form = LoginForm()
    error = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            try:
                username = User.objects.get(email=email, is_staff=True).username
            except User.DoesNotExist:
                username = None
            user = authenticate(request, username=username, password=password) if username else None
            if user:
                login(request, user)
                return redirect("admin_dashboard")
            error = "Wrong email or password!"
    return render(request, "library/admin_login.html", {"form": form, "error": error})


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful... You may login now!")
            return redirect("index")
    else:
        form = SignupForm()
    return render(request, "library/signup.html", {"form": form})


def forgot_password(request):
    """Send password reset link to user's email."""
    form = ForgotPasswordForm()
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.get(email=email)
            
            # Generate secure token
            token = base64.b64encode(f"{user.id}:{secrets.token_hex(16)}".encode()).decode()
            
            # Store token in session cache (in production, use a real token storage solution)
            request.session[f"reset_token_{user.id}"] = token
            request.session.set_expiry(3600)  # 1 hour
            
            # Send reset link via email
            reset_link = request.build_absolute_uri(reverse('reset_password', args=[user.id, token]))
            subject = "Password Reset Request"
            message = f"""Hello {user.first_name or user.username},

We received a request to reset your password. Click the link below to reset it:

{reset_link}

This link expires in 1 hour.

If you didn't request this, you can ignore this email.

Best regards,
Library Management System"""
            
            notify(subject, message, email)
            messages.success(request, "Password reset link has been sent to your email!")
            return redirect("index")
    
    return render(request, "library/forgot_password.html", {"form": form})


def reset_password(request, user_id, token):
    """Reset user password with token."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Invalid password reset link!")
        return redirect("index")
    
    # Verify token
    stored_token = request.session.get(f"reset_token_{user_id}")
    if not stored_token or stored_token != token:
        messages.error(request, "Invalid or expired password reset link!")
        return redirect("index")
    
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["new_password"]
            user.set_password(password)
            user.save()
            
            # Clear token from session
            if f"reset_token_{user_id}" in request.session:
                del request.session[f"reset_token_{user_id}"]
            
            messages.success(request, "Password reset successfully! Please login with your new password.")
            return redirect("index")
    else:
        form = ResetPasswordForm()
    
    return render(request, "library/reset_password.html", {"form": form, "user": user})


def user_logout(request):
    logout(request)
    return redirect("index")


# ---------- User dashboard ----------

@login_required
def user_dashboard(request):
    issued_count = IssuedBook.objects.filter(student=request.user, status=1).count()
    pending_requests = BookRequest.objects.filter(student=request.user, status=BookRequest.PENDING).count()
    return render(request, "library/user_dashboard.html", {
        "issued_count": issued_count,
        "pending_requests": pending_requests,
    })


@login_required
def view_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, "library/view_profile.html", {"profile": profile})


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            request.user.first_name = data["name"]
            request.user.email = data["email"]
            request.user.save()
            profile.mobile = data["mobile"]
            profile.address = data["address"]
            profile.save()
            messages.success(request, "Updated successfully...")
            return redirect("user_dashboard" if not request.user.is_staff else "admin_dashboard")
    else:
        form = ProfileEditForm(initial={
            "name": request.user.first_name,
            "email": request.user.email,
            "mobile": profile.mobile,
            "address": profile.address,
        })
    return render(request, "library/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            if request.user.check_password(form.cleaned_data["old_password"]):
                request.user.set_password(form.cleaned_data["new_password"])
                request.user.save()
                messages.success(request, "Password updated successfully. Please login again.")
                return redirect("index")
            else:
                messages.error(request, "Wrong current password!")
    else:
        form = ChangePasswordForm()
    return render(request, "library/change_password.html", {"form": form})


@login_required
def view_issued_books(request):
    issued = IssuedBook.objects.filter(student=request.user).select_related("book", "book__author")
    return render(request, "library/view_issued_books.html", {"issued": issued})


@login_required
def search_books(request):
    """Book catalogue with advanced search + filters + sorting + pagination."""
    q = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    author_id = request.GET.get("author", "")
    availability = request.GET.get("availability", "")  # "available", "unavailable", or ""
    sort_by = request.GET.get("sort", "name")  # name, price_low, price_high, newest

    books = Book.objects.select_related("author", "category").all()
    
    # Apply search filter
    if q:
        books = books.filter(Q(name__icontains=q) | Q(author__name__icontains=q) | Q(book_no__icontains=q))
    
    # Apply category filter
    if category_id:
        books = books.filter(category_id=category_id)
    
    # Apply author filter
    if author_id:
        books = books.filter(author_id=author_id)
    
    # Apply availability filter
    if availability == "available":
        books = books.filter(copies_available__gt=0)
    elif availability == "unavailable":
        books = books.filter(copies_available=0)
    
    # Apply sorting
    if sort_by == "price_low":
        books = books.order_by("price")
    elif sort_by == "price_high":
        books = books.order_by("-price")
    elif sort_by == "newest":
        books = books.order_by("-id")
    else:
        books = books.order_by("name")

    paginator = Paginator(books, 6)
    page_obj = paginator.get_page(request.GET.get("page"))
    
    # Build query string for pagination
    qs_parts = []
    if q:
        qs_parts.append(f"q={q}")
    if category_id:
        qs_parts.append(f"category={category_id}")
    if author_id:
        qs_parts.append(f"author={author_id}")
    if availability:
        qs_parts.append(f"availability={availability}")
    if sort_by != "name":
        qs_parts.append(f"sort={sort_by}")
    qs = ("&" + "&".join(qs_parts)) if qs_parts else ""

    return render(request, "library/search_books.html", {
        "page_obj": page_obj,
        "q": q,
        "qs": qs,
        "categories": Category.objects.all(),
        "authors": Author.objects.all(),
        "selected_category": category_id,
        "selected_author": author_id,
        "selected_availability": availability,
        "selected_sort": sort_by,
        "total_results": paginator.count,
    })


@login_required
def reserve_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if book.copies_available > 0:
        messages.info(request, "This book currently has copies available — ask the librarian to issue it directly.")
    else:
        BookRequest.objects.create(request_type=BookRequest.RESERVATION, student=request.user, book=book)
        messages.success(request, f"Reservation request submitted for '{book.name}'.")
    return redirect("search_books")


@login_required
def request_renewal(request, pk):
    issued = get_object_or_404(IssuedBook, pk=pk, student=request.user, status=1)
    if BookRequest.objects.filter(issued_book=issued, status=BookRequest.PENDING).exists():
        messages.info(request, "You already have a pending renewal request for this book.")
    else:
        BookRequest.objects.create(request_type=BookRequest.RENEWAL, student=request.user, book=issued.book, issued_book=issued)
        messages.success(request, "Renewal request submitted for admin approval.")
    return redirect("view_issued_books")


@login_required
def book_detail(request, book_id):
    """Display book details with ratings and reviews"""
    book = get_object_or_404(Book, pk=book_id)
    reviews = book.reviews.filter(is_approved=True).order_by('-created_at')
    
    # Calculate average rating
    avg_rating = None
    total_ratings = 0
    if book.ratings.exists():
        from django.db.models import Avg
        avg_rating = book.ratings.aggregate(Avg('rating'))['rating__avg']
        total_ratings = book.ratings.count()
    
    # Get user's rating if exists
    user_rating = None
    if request.user.is_authenticated:
        user_rating = book.ratings.filter(user=request.user).first()
    
    # Handle POST request for rating
    if request.method == "POST" and request.user.is_authenticated:
        action = request.POST.get('action')
        
        if action == 'rate':
            rating_value = int(request.POST.get('rating', 5))
            BookRating.objects.update_or_create(
                book=book,
                user=request.user,
                defaults={'rating': rating_value}
            )
            messages.success(request, f"You rated this book {rating_value}★")
            return redirect('book_detail', book_id=book_id)
        
        elif action == 'review':
            form = BookReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.book = book
                review.user = request.user
                review.save()
                messages.success(request, "Your review has been posted and is pending admin approval!")
                return redirect('book_detail', book_id=book_id)
    else:
        form = BookReviewForm()
    
    return render(request, "library/book_detail.html", {
        "book": book,
        "reviews": reviews,
        "avg_rating": avg_rating,
        "total_ratings": total_ratings,
        "user_rating": user_rating,
        "form": form,
    })


@login_required
def my_requests(request):
    reqs = BookRequest.objects.filter(student=request.user).select_related("book").order_by("-requested_at")
    return render(request, "library/my_requests.html", {"requests": reqs})


def book_qr(request, pk):
    """Generates a QR code PNG on the fly, encoding the book's accession number."""
    book = get_object_or_404(Book, pk=pk)
    img = qrcode.make(f"BOOK:{book.book_no}")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")


@login_required
def download_book_pdf(request, book_id):
    """Allow authenticated users to download book PDF"""
    book = get_object_or_404(Book, pk=book_id)
    
    if not book.pdf_file:
        messages.error(request, "This book does not have a PDF file available.")
        return redirect('book_detail', book_id=book_id)
    
    file_path = book.pdf_file.path
    response = HttpResponse(book.pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{book.name}.pdf"'
    return response


# ---------- Admin dashboard ----------

@user_passes_test(is_admin, login_url="admin_login")
def admin_dashboard(request):
    category_counts = Counter(Book.objects.values_list("category__name", flat=True))
    from django.db.models.functions import TruncMonth
    from django.db.models import Count
    monthly = (
        IssuedBook.objects.annotate(month=TruncMonth("issue_date"))
        .values("month").annotate(total=Count("id")).order_by("month")
    )
    context = {
        "user_count": User.objects.filter(is_staff=False).count(),
        "book_count": Book.objects.count(),
        "category_count": Category.objects.count(),
        "author_count": Author.objects.count(),
        "issued_count": IssuedBook.objects.filter(status=1).count(),
        "defaulter_count": sum(1 for i in IssuedBook.objects.filter(status=1) if i.is_overdue()),
        "pending_request_count": BookRequest.objects.filter(status=BookRequest.PENDING).count(),
        "category_labels": json.dumps(list(category_counts.keys())),
        "category_data": json.dumps(list(category_counts.values())),
        "month_labels": json.dumps([m["month"].strftime("%b %Y") for m in monthly]),
        "month_data": json.dumps([m["total"] for m in monthly]),
    }
    return render(request, "library/admin_dashboard.html", context)


@user_passes_test(is_admin, login_url="admin_login")
def registered_users(request):
    users = User.objects.filter(is_staff=False).select_related("profile").order_by("first_name")
    paginator = Paginator(users, 8)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "library/registered_users.html", {"page_obj": page_obj, "qs": ""})


@user_passes_test(is_admin, login_url="admin_login")
def add_book(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Book added successfully!")
            return redirect("manage_books")
    else:
        form = BookForm()
    return render(request, "library/add_book.html", {"form": form})


@user_passes_test(is_admin, login_url="admin_login")
def manage_books(request):
    q = request.GET.get("q", "").strip()
    books = Book.objects.select_related("author", "category").all().order_by("name")
    if q:
        books = books.filter(Q(name__icontains=q) | Q(author__name__icontains=q) | Q(book_no__icontains=q))
    paginator = Paginator(books, 8)
    page_obj = paginator.get_page(request.GET.get("page"))
    qs = f"&q={q}" if q else ""
    return render(request, "library/manage_books.html", {"page_obj": page_obj, "q": q, "qs": qs})


@user_passes_test(is_admin, login_url="admin_login")
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Book updated successfully!")
            return redirect("manage_books")
    else:
        form = BookForm(instance=book)
    return render(request, "library/add_book.html", {"form": form, "editing": True, "book": book})


@user_passes_test(is_admin, login_url="admin_login")
def delete_book(request, pk):
    get_object_or_404(Book, pk=pk).delete()
    messages.success(request, "Book removed.")
    return redirect("manage_books")


@user_passes_test(is_admin, login_url="admin_login")
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully!")
            return redirect("manage_categories")
    else:
        form = CategoryForm()
    return render(request, "library/add_category.html", {"form": form})


@user_passes_test(is_admin, login_url="admin_login")
def manage_categories(request):
    categories = Category.objects.all()
    return render(request, "library/manage_categories.html", {"categories": categories})


@user_passes_test(is_admin, login_url="admin_login")
def delete_category(request, pk):
    get_object_or_404(Category, pk=pk).delete()
    return redirect("manage_categories")


@user_passes_test(is_admin, login_url="admin_login")
def add_author(request):
    if request.method == "POST":
        form = AuthorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Author added successfully!")
            return redirect("manage_authors")
    else:
        form = AuthorForm()
    return render(request, "library/add_author.html", {"form": form})


@user_passes_test(is_admin, login_url="admin_login")
def manage_authors(request):
    authors = Author.objects.all()
    return render(request, "library/manage_authors.html", {"authors": authors})


@user_passes_test(is_admin, login_url="admin_login")
def delete_author(request, pk):
    get_object_or_404(Author, pk=pk).delete()
    return redirect("manage_authors")


@user_passes_test(is_admin, login_url="admin_login")
def issue_book(request):
    if request.method == "POST":
        form = IssueBookForm(request.POST)
        if form.is_valid():
            book = form.cleaned_data["book"]
            student = form.cleaned_data["student"]
            IssuedBook.objects.create(book=book, student=student)
            book.copies_available -= 1
            book.save()
            notify(
                f"'{book.name}' has been issued to you",
                f"Hi {student.first_name or student.username},\n\n"
                f"'{book.name}' has been issued to you. Please return it within 14 days "
                f"to avoid a late fine of Rs. {FINE_PER_DAY}/day.\n\n- Library",
                student.email,
            )
            messages.success(request, f"'{book.name}' issued to {student.first_name or student.username}.")
            return redirect("issue_book")
    else:
        form = IssueBookForm()
    all_issued = IssuedBook.objects.filter(status=1).select_related("book", "student")
    return render(request, "library/issue_book.html", {"form": form, "all_issued": all_issued})


@user_passes_test(is_admin, login_url="admin_login")
def return_book(request, pk):
    issued = get_object_or_404(IssuedBook, pk=pk)
    if issued.status == 1:
        issued.status = 0
        issued.return_date = timezone.now()
        fine = issued.calculate_fine()
        issued.save()
        issued.book.copies_available += 1
        issued.book.save()
        if fine:
            messages.success(request, f"Book marked as returned. Late fine due: Rs. {fine}.")
        else:
            messages.success(request, "Book marked as returned. No fine due.")
    return redirect("issue_book")


@user_passes_test(is_admin, login_url="admin_login")
def defaulter_list(request):
    """Admin report: currently issued books that are past their due date, with fines."""
    overdue = [i for i in IssuedBook.objects.filter(status=1).select_related("book", "student") if i.is_overdue()]
    overdue.sort(key=lambda i: i.due_date)
    return render(request, "library/defaulter_list.html", {"overdue": overdue})


@user_passes_test(is_admin, login_url="admin_login")
def manage_requests(request):
    pending = BookRequest.objects.filter(status=BookRequest.PENDING).select_related("book", "student", "issued_book")
    resolved = BookRequest.objects.exclude(status=BookRequest.PENDING).select_related("book", "student").order_by("-resolved_at")[:20]
    return render(request, "library/manage_requests.html", {"pending": pending, "resolved": resolved})


@user_passes_test(is_admin, login_url="admin_login")
def resolve_request(request, pk, action):
    req = get_object_or_404(BookRequest, pk=pk)
    if req.status != BookRequest.PENDING:
        return redirect("manage_requests")

    if action == "approve":
        req.status = BookRequest.APPROVED
        if req.request_type == BookRequest.RENEWAL and req.issued_book:
            req.issued_book.due_date = req.issued_book.due_date + timezone.timedelta(days=7)
            req.issued_book.save()
            notify("Your book renewal was approved", f"Your due date has been extended by 7 days.", req.student.email)
        elif req.request_type == BookRequest.RESERVATION:
            notify("Your book reservation was approved", f"'{req.book.name}' is now reserved for you — visit the library to collect it.", req.student.email)
        messages.success(request, "Request approved.")
    else:
        req.status = BookRequest.REJECTED
        notify("Your library request was declined", f"Your {req.get_request_type_display().lower()} request for '{req.book.name}' was declined.", req.student.email)
        messages.info(request, "Request rejected.")

    req.resolved_at = timezone.now()
    req.save()
    return redirect("manage_requests")
