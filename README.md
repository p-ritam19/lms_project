# Library Management System (Django)

A Django rebuild of the classic PHP/MySQL Library Management System project
(users, admins, authors, categories, books, and book issuing), extended with
search, fines, book requests, a REST API, and more.

## Core features (from the original project)
- **User side:** signup, login, dashboard, view/edit profile, change password,
  view issued books.
- **Admin side:** separate admin login, dashboard with stats, add/manage
  books, categories, authors, issue/return books, view registered users.
- Django's ORM replaces raw SQL, and Django's auth system (with `is_staff`
  distinguishing admins from regular users) replaces PHP session-based login.
- Bootstrap 5 (bundled locally, no CDN required) for styling.

## Added features (beyond the original)
- **Book search & filter** — members can search/filter the catalogue by
  title, author, book number, or category (`/books/`).
- **Pagination** — on Manage Books, Registered Users, and the book catalogue.
- **Admin dashboard charts** — books-by-category (pie) and books-issued-per-month
  (bar), rendered with Chart.js (bundled locally).
- **Overdue fines** — `IssuedBook.calculate_fine()` charges ₹2/day once a book
  is overdue; shown to both the student and the admin, and finalized when the
  book is marked returned.
- **Defaulter list** — a dedicated admin report (`/admin-dashboard/defaulters/`)
  listing every currently-overdue book, the student, and the fine owed.
- **Book cover images** — admins can upload a cover image per book
  (`Book.cover`, an `ImageField`); shown in the catalogue and Manage Books.
- **Email notifications** — an email is sent when a book is issued, and when
  a reservation/renewal request is approved or rejected. Uses Django's
  **console** email backend by default (prints to the terminal) so it works
  out of the box with no SMTP setup — swap `EMAIL_BACKEND` in `settings.py`
  for a real provider (e.g. SMTP, SendGrid) in production.
- **Book reservation & renewal requests** — a `BookRequest` model lets a
  member request a currently-unavailable book (reservation) or a due-date
  extension on a book they already have (renewal); admins approve/reject
  these from `/admin-dashboard/requests/`.
- **QR codes** — each book gets an on-the-fly generated QR code (encoding its
  accession number) shown next to it in Manage Books, using the `qrcode`
  package.
- **REST API** — a full JSON API under `/api/` (Django REST Framework):
  `/api/books/`, `/api/authors/`, `/api/categories/`, `/api/issued-books/`.
  Read access is open; write access requires an authenticated admin
  (`is_staff`); the issued-books endpoint is admin-only entirely. Useful as a
  foundation for a future mobile app.

## Project layout
```
lms_django/
├── manage.py
├── requirements.txt
├── lms_project/        # Django project settings/urls
└── library/             # Main app
    ├── models.py         # Author, Category, Book, Profile, IssuedBook, BookRequest
    ├── forms.py
    ├── views.py
    ├── urls.py
    ├── api_views.py, api_urls.py, serializers.py   # REST API
    ├── admin.py          # Django admin registration
    ├── static/library/   # Bundled Bootstrap + Chart.js (no CDN dependency)
    └── templates/library/
```

## Setup
```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # this becomes your first Admin login
python manage.py runserver
```

Then visit:
- `http://127.0.0.1:8000/` — user login / signup
- `http://127.0.0.1:8000/admin-login/` — admin login (use the superuser you created)
- `http://127.0.0.1:8000/books/` — browse/search the catalogue (as a logged-in member)
- `http://127.0.0.1:8000/api/books/` — REST API
- `http://127.0.0.1:8000/django-admin/` — Django's built-in admin site (optional, extra)

Emails print straight to the terminal running `runserver` — issue a book or
approve a request and watch the console.

## Notes / how it maps to the original PHP version
| Original (PHP/MySQL)                  | Django equivalent                                   |
|----------------------------------------|--------------------------------------------------------|
| `users` table + PHP sessions           | Django `User` model + `Profile` (mobile/address) + built-in auth |
| `admins` table                         | Django `User` with `is_staff=True`                   |
| `books`, `authors`, `category` tables  | `Book`, `Author`, `Category` models                   |
| `issued_books` table                   | `IssuedBook` model (tracks issue/due/return dates, fine) |
| Raw `mysqli_query()` calls             | Django ORM (querysets)                                |
| Plain HTML forms + manual validation   | Django `Form` / `ModelForm` with built-in validation  |

## Extending it further
- Real SMTP email delivery (swap `EMAIL_BACKEND` in `settings.py`).
- Fine payment tracking (there's already a `fine_paid` flag on `IssuedBook`,
  not yet wired to a payment flow).
- Swap SQLite for PostgreSQL/MySQL in `settings.py` `DATABASES` for production.
- A mobile app or admin panel consuming the `/api/` endpoints directly.
