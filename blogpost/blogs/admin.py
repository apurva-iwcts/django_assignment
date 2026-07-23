from django.contrib import admin

# import blogs
from blogs.models import User, Author, Category, BlogPost, Comment, AuthorDocs

admin.site.register(User)
admin.site.register(Author)
admin.site.register(Category)
admin.site.register(BlogPost)
admin.site.register(Comment)
admin.site.register(AuthorDocs)
