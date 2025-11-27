from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import UserViewSet
from . import views

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('admin/create-user/', views.admin_create_user, name='admin-create-user'),
    path('', include(router.urls)),
]