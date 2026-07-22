"""
URL configuration for blogpost project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
# from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

"""
title: Specifies the title of your API documentation.
default_version: Defines the version of your API. This is useful if you have multiple versions of your API, allowing you to differentiate between them.
description: Provides a brief description of your API. This can be an overview of what the API does, its key features, or any other relevant information.
terms_of_service: A URL pointing to the terms of service for your API. This is optional but can be included if you want to provide legal terms for using the API.
contact: Provides contact information for the API maintainers. This is typically used to provide an email address where users can send feedback or report issues.
license: Specifies the license under which the API is distributed. This can be important for users to understand the legal permissions they have when using the API.
"""

schema_view = get_schema_view(
   openapi.Info(
      title="blogs",
      default_version='v3',
      description="django practice",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@yourapi.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("blogs.urls")),
    # path("api/schema/",SpectacularAPIView.as_view(),name="schema",),  
    # path("api/redoc/",SpectacularRedocView.as_view(url_name="schema"), name="redoc",),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),  
]