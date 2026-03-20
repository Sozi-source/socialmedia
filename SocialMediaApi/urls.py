"""
URL configuration for SocialMediaApi project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('SocialApp.urls')),
]

# Serve media files in development - THIS IS CRITICAL
if settings.DEBUG:
    # Option 1: Using re_path (most reliable)
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
    
    # Option 2: Using static (fallback)
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

print(f"✅ Media serving configured for development")
print(f"📁 Media will be served from: {settings.MEDIA_ROOT}")