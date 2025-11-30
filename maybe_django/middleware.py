"""
Custom middleware for Maybe Django application
"""
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class StaticFilesCacheMiddleware(MiddlewareMixin):
    """
    Adds cache headers to static files served by Django.
    In production, static files should be served by the web server (nginx, etc.),
    but this middleware ensures proper cache headers during development.
    """
    
    def process_response(self, request, response):
        # Only add cache headers for static files
        if hasattr(request, 'path') and request.path.startswith(settings.STATIC_URL):
            # Set long cache for immutable assets (fonts, images)
            if any(request.path.endswith(ext) for ext in ['.woff2', '.woff', '.ttf', '.eot', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']):
                response['Cache-Control'] = 'public, max-age=31536000, immutable'
            # Set cache for CSS and JS files
            elif any(request.path.endswith(ext) for ext in ['.css', '.js']):
                response['Cache-Control'] = 'public, max-age=31536000'
            else:
                # Default cache for other static files
                response['Cache-Control'] = 'public, max-age=86400'  # 1 day
        
        return response

