from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # OCR proxy endpoint - moved to top to ensure it matches before other patterns
    path('api/ocr/', views.ocr_proxy, name='ocr_proxy'),
    
    path('admin/', admin.site.urls),
    path('api/access-control/', include('access_control.urls')),
    
    # Djoser URLs for authentication
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    
    # Accounts app URLs
    path('api/accounts/', include('accounts.urls')),
    
    path('api-token-auth/', obtain_auth_token),
] 

# Serve the index.html for all other routes using static file serving
urlpatterns += [re_path(r'^(?!api/|admin/|auth/|static/|media/).*$', TemplateView.as_view(template_name='index.html'))]

# Add this line to ensure static files are served in development
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)