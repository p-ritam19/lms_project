from django import forms
from django.contrib.auth.models import User
from .models import Profile, Book, Author, Category, IssuedBook, BookRating, BookReview

TEXT_ATTRS = {"class": "form-control"}
SELECT_ATTRS = {"class": "form-select"}


class BootstrapMixin:
    """Adds Bootstrap CSS classes to every field's widget automatically."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                widget.attrs.setdefault("class", "form-control")


class SignupForm(BootstrapMixin, forms.Form):
    name = forms.CharField(max_length=150, label="Full Name")
    email = forms.EmailField(label="Email ID")
    password = forms.CharField(widget=forms.PasswordInput)
    mobile = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["email"],
            email=data["email"],
            password=data["password"],
            first_name=data["name"],
        )
        Profile.objects.create(user=user, mobile=data["mobile"], address=data["address"])
        return user


class LoginForm(BootstrapMixin, forms.Form):
    email = forms.EmailField(label="Email ID")
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileEditForm(BootstrapMixin, forms.Form):
    name = forms.CharField(max_length=150, label="Full Name")
    email = forms.EmailField(label="Email ID")
    mobile = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)


class ChangePasswordForm(BootstrapMixin, forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")


class AuthorForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Author
        fields = ["name"]


class CategoryForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class BookForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Book
        fields = ["name", "author", "category", "book_no", "price", "copies_available", "cover"]


class IssueBookForm(BootstrapMixin, forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.filter(copies_available__gt=0))
    student = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=False))


class ForgotPasswordForm(BootstrapMixin, forms.Form):
    email = forms.EmailField(label="Email ID")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No account found with this email address.")
        return email


class ResetPasswordForm(BootstrapMixin, forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        confirm = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data


class BookRatingForm(forms.ModelForm):
    class Meta:
        model = BookRating
        fields = ['rating']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f"{i}★") for i in range(1, 6)])
        }


class BookReviewForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = BookReview
        fields = ['rating', 'title', 'content']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f"{i}★") for i in range(1, 6)]),
            'title': forms.TextInput(attrs={'placeholder': 'Review title...'}),
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your thoughts about this book...'})
        }
        labels = {
            'rating': 'Rating',
            'title': 'Title',
            'content': 'Your Review'
        }
