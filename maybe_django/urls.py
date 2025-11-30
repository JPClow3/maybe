"""
URL configuration for maybe_django project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Public files (manifest, browserconfig, etc.)
    path('site.webmanifest', core_views.serve_public_file, {'filename': 'site.webmanifest'}, name='site_webmanifest'),
    path('browserconfig.xml', core_views.serve_public_file, {'filename': 'browserconfig.xml'}, name='browserconfig'),
    path('robots.txt', core_views.serve_public_file, {'filename': 'robots.txt'}, name='robots'),
    path('', include('core.urls')),
    path('', include('finance.urls')),
    path('', include('investments.urls')),
    path('', include('imports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error handlers
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
handler403 = 'core.views.handler403'

