from rest_framework.routers import DefaultRouter
from .api_views import AuthorViewSet, CategoryViewSet, BookViewSet, IssuedBookViewSet

router = DefaultRouter()
router.register("authors", AuthorViewSet, basename="api-author")
router.register("categories", CategoryViewSet, basename="api-category")
router.register("books", BookViewSet, basename="api-book")
router.register("issued-books", IssuedBookViewSet, basename="api-issuedbook")

urlpatterns = router.urls
