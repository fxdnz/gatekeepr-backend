from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import UserAccount
from .serializers import (
    UserCreateSerializer, 
    UserProfileSerializer, 
    AdminUserUpdateSerializer,
    UserListSerializer  # Import the new serializer
)
from .permissions import CanManageUsers, CanAccessUserDetail

class UserViewSet(viewsets.ModelViewSet):
    queryset = UserAccount.objects.all()
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminUserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer  # Use UserListSerializer for listing
        else:
            return UserProfileSerializer
    
    def is_admin_user(self):
        """Check if current user is admin or superuser"""
        user = self.request.user
        return user.is_superuser or user.role in ['system_admin', 'user_admin']
    
    def get_queryset(self):
        """
        Personnel can only see themselves, admins can see all users
        """
        user = self.request.user
        if self.is_admin_user():
            return UserAccount.objects.all().order_by('email')
        else:
            # Personnel can only see their own account
            return UserAccount.objects.filter(id=user.id)
    
    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        """
        if self.action == 'retrieve':
            permission_classes = [permissions.IsAuthenticated, CanAccessUserDetail]
        else:
            permission_classes = [permissions.IsAuthenticated, CanManageUsers]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Endpoint for users to get their own profile (READ-ONLY)
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)