# Library Management System (Django)

A comprehensive Library Management System built with Django that includes user and admin functionalities (users, admins, authors, categories, books, and book issuing) using Django's built-in authentication, ORM, and forms.

## Features
- **User side:** signup, login, dashboard, view/edit profile, change password, view issued books.
- **Admin side:** separate admin login, dashboard with stats (users, books, categories, authors, issued books), add/manage books, categories, authors, issue/return books, view registered users.
- Django's Object-Relational Mapper (ORM) for efficient database queries.
- Django's built-in authentication system with `is_staff` distinguishing admins from regular users.
- Bootstrap 5 (via CDN) for responsive and modern styling.

## Project Layout
```
lms_django/
├── manage.py
├── requirements.txt
├── lms_project/        # Django project settings/urls
└── library/            # Main app
    ├── models.py       # Author, Category, Book, Profile, IssuedBook
    ├── forms.py
    ├── views.py
    ├── urls.py
    ├── admin.py        # Django admin registration
    ├── static/         # CSS, Images, JavaScript
    └── templates/library/
```

## Setup
```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # Create your first Admin login
python manage.py runserver
```

Then visit:
- `http://127.0.0.1:8000/` — User login / signup
- `http://127.0.0.1:8000/admin-login/` — Admin login (use the superuser you created)
- `http://127.0.0.1:8000/django-admin/` — Django's built-in admin site

## Database Models
- **User** — Django's built-in User model for authentication
- **Profile** — User additional information (mobile, address)
- **Author** — Book authors
- **Category** — Book categories
- **Book** — Book details and inventory
- **IssuedBook** — Track issued books with issue, due, and return dates

## Key Technologies
- **Backend:** Django 6.0+
- **Database:** SQLite (default), easily swap for PostgreSQL/MySQL
- **Frontend:** HTML5, CSS3, Bootstrap 5
- **Authentication:** Django built-in auth system

## Future Enhancements
- Add search/filter for books (by title, author, category)
- Add fines for overdue books
- Add pagination to tables (Manage Books, Registered Users)
- Integrate email notifications for book issues/returns
- Add book recommendations based on user history

