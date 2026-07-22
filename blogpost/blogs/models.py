from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    join_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class AuthorDocs(models.Model):
    author = models.OneToOneField(
        "Author",
        on_delete=models.CASCADE,
        related_name="docs"
    )
    biography = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to="authors/profile_pictures/",
        blank=True,
        null=True,
    )
    document = models.FileField(
        upload_to="authors/docs/",
        blank=True,
        null=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"About {self.author.name}"
    

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon_url = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=200, unique=True)
    content = models.TextField()

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    tags = models.CharField(max_length=200, blank=True)

    featured_image = models.ImageField(
        upload_to="blog/featured/",
        blank=True,
        null=True,
    )

    publication_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publication_date"]
        indexes = [
            models.Index(fields=["is_published", "is_archived"]),
            models.Index(fields=["-view_count"]),
            models.Index(fields=["-publication_date"]),
        ]

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comments",
        help_text="Set when the commenter is authenticated; enables ownership checks.",
    )

    author_name = models.CharField(max_length=100)
    email = models.EmailField()
    comment = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    moderated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["post"]),
        ]

    def __str__(self):
        return f"Comment by {self.author_name} on {self.post_id}"
    