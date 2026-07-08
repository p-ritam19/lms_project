from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin-login/", views.admin_login, name="admin_login"),
    path("signup/", views.signup, name="signup"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/<int:user_id>/<str:token>/", views.reset_password, name="reset_password"),
    path("logout/", views.user_logout, name="logout"),

    # user
    path("dashboard/", views.user_dashboard, name="user_dashboard"),
    path("profile/", views.view_profile, name="view_profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/change-password/", views.change_password, name="change_password"),
    path("my-books/", views.view_issued_books, name="view_issued_books"),
    path("books/", views.search_books, name="search_books"),
    path("books/<int:book_id>/", views.book_detail, name="book_detail"),
    path("books/<int:book_id>/download/", views.download_book_pdf, name="download_book_pdf"),
    path("books/<int:pk>/reserve/", views.reserve_book, name="reserve_book"),
    path("my-books/<int:pk>/renew/", views.request_renewal, name="request_renewal"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("books/<int:pk>/qr/", views.book_qr, name="book_qr"),

    # admin
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/users/", views.registered_users, name="registered_users"),

    path("admin-dashboard/books/add/", views.add_book, name="add_book"),
    path("admin-dashboard/books/", views.manage_books, name="manage_books"),
    path("admin-dashboard/books/<int:pk>/edit/", views.edit_book, name="edit_book"),
    path("admin-dashboard/books/<int:pk>/delete/", views.delete_book, name="delete_book"),

    path("admin-dashboard/categories/add/", views.add_category, name="add_category"),
    path("admin-dashboard/categories/", views.manage_categories, name="manage_categories"),
    path("admin-dashboard/categories/<int:pk>/delete/", views.delete_category, name="delete_category"),

    path("admin-dashboard/authors/add/", views.add_author, name="add_author"),
    path("admin-dashboard/authors/", views.manage_authors, name="manage_authors"),
    path("admin-dashboard/authors/<int:pk>/delete/", views.delete_author, name="delete_author"),

    path("admin-dashboard/issue-book/", views.issue_book, name="issue_book"),
    path("admin-dashboard/issue-book/<int:pk>/return/", views.return_book, name="return_book"),
    path("admin-dashboard/defaulters/", views.defaulter_list, name="defaulter_list"),

    path("admin-dashboard/requests/", views.manage_requests, name="manage_requests"),
    path("admin-dashboard/requests/<int:pk>/<str:action>/", views.resolve_request, name="resolve_request"),
]
