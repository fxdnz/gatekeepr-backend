
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('access_control.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('api-token-auth/', obtain_auth_token),
] 

# Serve the index.html for all other routes using static file serving
urlpatterns += [re_path(r'^.*$', TemplateView.as_view(template_name='index.html'))]

# Add this line to ensure static files are served in development
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
