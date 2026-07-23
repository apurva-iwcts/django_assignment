from datetime import timedelta

from django.db.models import Avg, Count
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate

from blogs.models import Author, Category, BlogPost, Comment, AuthorDocs, User
from blogs.serializers import (
    AuthorDocsCreateSerializer,
    AuthorDocsListSerializer,
    AuthorDocsSerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostCreateSerializer,
    BlogPostUpdateSerializer,
    AuthorSerializer,
    AuthorCreateSerializer,
    AuthorUpdateSerializer,
    CategorySerializer,
    CategoryCreateSerializer,
    CommentSerializer,
    CommentDetailSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
    UserRegisterSerializer,
    UserSerializer,
)

class UserRegistrationView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    http_method_names = ["post"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.get(user=user)
        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )
    
class UserLoginView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ["post", "get", "put", "delete"]
    action_serializers = {
        "list": UserSerializer,
        "retrieve": UserSerializer,
        "create": UserSerializer,
        "update": UserSerializer,
    }
    def create(self, request):
        user = authenticate(username=request.data['username'], password=request.data['password'])
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        else:
            return Response({'error': 'Invalid credentials'}, status=401)


class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostListSerializer
    # permission_classes = [IsAuthenticated]
    
    http_method_names = ["get", "post", "put", "delete"]
    
    action_serializers = {
        "list": BlogPostListSerializer,
        "retrieve": BlogPostDetailSerializer,
        "create": BlogPostCreateSerializer,
        "update": BlogPostUpdateSerializer,
    }

    def get_queryset(self):
        queryset = BlogPost.objects.select_related("author", "category")

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("comments")
        elif self.action == "list":
            queryset = queryset.only(
                "id", "title", "publication_date", "view_count",
                "content", "featured_image", "author__name", "category__name",
            ).filter(is_published=True, is_archived=False)

        return queryset

    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)

    def create(self, request, *args, **kwargs):
        '''
        Create a new blog post and associate it with the authenticated user's author profile.
        '''
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user.author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        BlogPost.objects.filter(pk=instance.pk).update(
            view_count=instance.view_count + 1
        )
        instance.refresh_from_db(fields=["view_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        posts = self.get_queryset().order_by("-view_count")[:10]
        return Response(BlogPostListSerializer(posts, many=True).data)

    @action(detail=False, methods=["get"])
    def recent(self, request):
        last_week = timezone.now() - timedelta(days=7)
        posts = self.get_queryset().filter(publication_date__gte=last_week)
        return Response(BlogPostListSerializer(posts, many=True).data)

    @action(detail=False, methods=["get"], url_path=r"author/(?P<author_id>[^/.]+)")
    def by_author(self, request, author_id):
        posts = self.get_queryset().filter(author_id=author_id)
        return Response(BlogPostListSerializer(posts, many=True).data)

    @action(detail=False, methods=["get"])
    def trending_categories(self, request):
        categories = (
            BlogPost.objects.values("category__id", "category__name")
            .annotate(post_count=Count("id"))
            .order_by("-post_count")
        )
        return Response(categories)

    @action(detail=False, methods=["get"])
    def drafts(self, request):
        posts = BlogPost.objects.select_related("author", "category").filter(
            is_published=False, is_archived=False
        )
        return Response(BlogPostListSerializer(posts, many=True).data)

    @action(detail=False, methods=["get"])
    def archived(self, request):
        posts = BlogPost.objects.select_related("author", "category").filter(
            is_archived=True
        )
        return Response(BlogPostListSerializer(posts, many=True).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        post = self.get_object()
        if post.is_published:
            return Response(
                {"message": "Post is already published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        post.is_published = True
        post.publication_date = timezone.now()
        post.save()
        return Response(BlogPostDetailSerializer(post).data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        post = self.get_object()
        if post.is_archived:
            return Response(
                {"message": "Post is already archived."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        post.is_archived = True
        post.save()
        return Response({"message": "Post archived successfully."})



class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    # permission_classes = [IsAuthenticated]
    
    http_method_names = ["get", "post", "put", "delete"]
    
    action_serializers = {
        "retrieve": AuthorSerializer,
        "create": AuthorCreateSerializer,
        "update": AuthorUpdateSerializer,
        "list": AuthorSerializer,
    }

    def get_queryset(self):
        queryset = Author.objects.all()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("posts")
        return queryset

    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]
    action_serializers = {
        "retrieve": CategorySerializer,
        "create": CategoryCreateSerializer,
        "update": CategoryCreateSerializer,
        "list": CategorySerializer,
    }

    def get_queryset(self):
        queryset = Category.objects.annotate(post_count=Count("posts"))
        ordering = self.request.query_params.get("ordering")
        if ordering == "post_count":
            queryset = queryset.order_by("-post_count")
        return queryset

    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)


    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.posts.exists() and request.query_params.get("force") != "true":
            return Response(
                {
                    "message": (
                        f"Category has {category.posts.count()} post(s). "
                        "Reassign them first, or retry with ?force=true to "
                        "delete anyway (posts will cascade-delete)."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def with_post_counts(self, request):
        categories = self.get_queryset().order_by("-post_count")
        data = [
            {"id": c.id, "name": c.name, "post_count": c.post_count}
            for c in categories
        ]
        return Response(data)

    @action(detail=True, methods=["get"])
    def posts(self, request, pk=None):
        category = self.get_object()
        posts = category.posts.filter(is_published=True, is_archived=False)
        return Response(BlogPostListSerializer(posts, many=True).data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    # permission_classes = [IsAuthenticated]

    http_method_names = ["get", "post", "put", "delete"]

    action_serializers = {
        "retrieve": CommentDetailSerializer,
        "create": CommentCreateSerializer,
        "update": CommentUpdateSerializer,
        "list": CommentSerializer,
    }

    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)

    def get_queryset(self):
        queryset = Comment.objects.select_related("post")

        post_id = self.request.query_params.get("post_id")
        if post_id:
            queryset = queryset.filter(post_id=post_id)

        if self.action == "list":
            queryset = queryset.filter(post__is_published=True)

        return queryset

    @action(detail=False, methods=["get"], url_path=r"post/(?P<post_id>[^/.]+)")
    def by_post(self, request, post_id):
        comments = self.get_queryset().filter(post_id=post_id)
        serializer = CommentDetailSerializer(
            comments,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def top_rated(self, request):
        comments = self.get_queryset().filter(rating__gte=4).order_by("-rating")
        serializer = CommentDetailSerializer(
            comments,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path=r"post/(?P<post_id>[^/.]+)/average-rating",
    )
    def average_rating(self, request, post_id):
        result = self.get_queryset().filter(
            post_id=post_id
        ).aggregate(
            avg_rating=Avg("rating"),
            total=Count("id"),
        )
        return Response(result)
    
class AuthorDocsViewSet(viewsets.ModelViewSet):
    queryset = AuthorDocs.objects.all()
    serializer_class = AuthorDocsSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    http_method_names = ["get", "post", "put", "delete"]
    
    action_serializers = {
        "list": AuthorDocsListSerializer,
        "retrieve": AuthorDocsSerializer,
        "create": AuthorDocsCreateSerializer,
        "update": AuthorDocsCreateSerializer,
    }

    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        queryset = AuthorDocs.objects.all()

        if self.action == "list":
            queryset = queryset.all()
        return queryset

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file = serializer.validated_data["document"]
        img = serializer.validated_data["profile_picture"]
        return Response({
            **serializer.data,
            "imagename": img.name,
            "imagesize": img.size,
            "filename": file.name,
            "filesize": file.size,
        })
        