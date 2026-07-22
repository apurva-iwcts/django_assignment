from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AuthorViewSet, BlogPostViewSet, CategoryViewSet, CommentViewSet, AuthorDocsViewSet, UserRegistrationView, UserLoginView

router = DefaultRouter()
router.register(r"posts", BlogPostViewSet, basename="post")
router.register(r"authors", AuthorViewSet, basename="author")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"comments", CommentViewSet, basename="comment")
# router.register(r"users", UserViewSet, basename="user")
router.register(r"register", UserRegistrationView, basename="register")
router.register(r"login", UserLoginView, basename="login")
router.register(r"author-docs", AuthorDocsViewSet, basename="author-docs")

urlpatterns = [
    path("", include(router.urls)),
]