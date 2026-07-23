
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import Author, Category, BlogPost, Comment, AuthorDocs, User

class UserSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = User
        fields = ["id", "username", "full_name", "email", "is_active", "date_joined"]
  
class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "full_name", "email", "password"]
        extra_kwargs = {
            'password': {"write_only": True}
        }

    def validate_username(self, username):
        if User.objects.filter(username=username).exists():
            detail = {
                "detail": "User Already exist!"
            }
            raise ValidationError(detail=detail)
        return username

    def validate(self, instance):
        if User.objects.filter(email=instance['email']).exists():
            raise ValidationError({"message": "Email already taken!"})
        return instance
    
    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        Token.objects.create(user=user)
        return user      
# class UserRegisterSerializer(serializers.ModelSerializer):
#     id = serializers.PrimaryKeyRelatedField(read_only=True)
#     class Meta:
#         model = User
#         fields = ["id", "username", "full_name", "email", "password"]
#         extra_kwargs = {
#             'password': {"write_only": True}
#         }

#     def validate_username(self, username):
#         if User.objects.filter(username=username).exists():
#             detail = {
#                 "detail": "User Already exist!"
#             }
#             raise ValidationError(detail=detail)
#         return username

#     def validate(self, instance):
#         if User.objects.filter(email=instance['email']).exists():
#             raise ValidationError({"message": "Email already taken!"})
#         return instance
    
#     def create(self, validated_data):
#         password = validated_data.pop("password")
#         user = User(**validated_data)
#         user.set_password(password)
#         user.save()
#         Token.objects.create(user=user)
#         return user


class CategorySerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = ["id", "name", "post_count"]

    def get_post_count(self, obj):
        return getattr(obj, "post_count", None) or obj.posts.count()


class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "description", "icon_url"]

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio", "email"]


class AuthorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name", "email", "bio"]

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value


class AuthorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name", "bio"]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "author_name", "comment", "rating", "created_at"]


class CommentDetailSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source="post.title", read_only=True)
    class Meta:
        model = Comment
        fields = [
            "id", "post", "post_title", "author_name", "email", "comment", "rating", "created_at",
        ]


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["post", "author_name", "email", "comment", "rating"]

    def validate_comment(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Comment must be at least 5 characters.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)


class CommentUpdateSerializer(serializers.ModelSerializer):
    """Owners can only edit content/rating, not approval/flag state."""
    class Meta:
        model = Comment
        fields = ["comment", "rating"]

    def validate_comment(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Comment must be at least 5 characters.")
        return value


class BlogPostListSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.name", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)
    excerpt = serializers.SerializerMethodField()
    class Meta:
        model = BlogPost
        fields = [
            "id", "title", "author", "category",
            "publication_date", "view_count", "excerpt", "featured_image",
        ]

    def get_excerpt(self, obj):
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content


class BlogPostDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    class Meta:
        model = BlogPost
        fields = [
            "id", "title", "content", "author", "category", "tags",
            "featured_image", "publication_date", "is_published",
            "is_archived", "view_count", "comments", "created_at", "updated_at",
        ]

    def get_comments(self, obj):
        request = self.context.get("request")
        qs = obj.comments.all()
        if not (request and request.user.is_staff):
            qs = qs.filter(post__is_published=True)
        return CommentSerializer(qs, many=True).data


class BlogPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = [
            "title", "content", "author", "category", "tags",
            "featured_image", "publication_date", "is_published",
        ]

    def validate_title(self, value):
        if not (5 <= len(value) <= 200):
            raise serializers.ValidationError(
                "Title must be between 5 and 200 characters."
            )
        return value

    def validate_content(self, value):
        if len(value) < 100:
            raise serializers.ValidationError(
                "Content must contain at least 100 characters."
            )
        return value

    def validate_author(self, value):
        if value is None:
            raise serializers.ValidationError("Author must exist.")
        return value

    def validate(self, attrs):
        is_published = attrs.get(
            "is_published",
            getattr(self.instance, "is_published", False)
        )
        publication_date = attrs.get(
            "publication_date",
            getattr(self.instance, "publication_date", None)
        )
        if is_published and publication_date and publication_date > timezone.now():
            raise serializers.ValidationError(
                {"publication_date": "Published posts cannot have a future publication date."}
            )
        return attrs


class BlogPostUpdateSerializer(BlogPostCreateSerializer):
    class Meta(BlogPostCreateSerializer.Meta):
        fields = [
            "title", "content", "category", "tags",
            "featured_image", "publication_date", "is_published", "is_archived",
        ]
        

class AuthorDocsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorDocs
        fields = ["id", "author", "biography", "profile_picture", "document", "uploaded_at"]
        
class AuthorDocsListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)
    class Meta:
        model = AuthorDocs
        fields = ["id", "author", "author_name", "biography", "profile_picture", "document", "uploaded_at"]
        
class AuthorDocsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorDocs
        fields = ["author", "biography", "profile_picture", "document"]

    def validate(self, instance):
        if not Author.objects.filter(id=instance['author'].id).exists():
            raise ValidationError({"message": "Author does not exist!"})
        return instance
     