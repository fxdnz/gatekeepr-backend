from rest_framework import permissions

class CanManageUsers(permissions.BasePermission):
    """
    Custom permission to allow full user management:
    - Superusers (is_superuser=True) 
    - system_admin role
    - user_admin role
    """
    def has_permission(self, request, view):
        # For list, create actions - only admins can list all users or create
        if request.method == 'POST':
            # Only admins can create users
            return bool(
                request.user and 
                request.user.is_authenticated and
                (request.user.is_superuser or 
                 request.user.role in ['system_admin', 'user_admin'])
            )
        elif request.method == 'GET':
            # Everyone can access GET, but object-level controls what they see
            return bool(request.user and request.user.is_authenticated)
        elif request.method in ['PUT', 'PATCH', 'DELETE']:
            # Only admins can update/delete
            return bool(
                request.user and 
                request.user.is_authenticated and
                (request.user.is_superuser or 
                 request.user.role in ['system_admin', 'user_admin'])
            )
        return True
    
    def has_object_permission(self, request, view, obj):
        # For retrieve - users can see their own data, admins can see all
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return (obj == request.user or 
                    request.user.is_superuser or
                    request.user.role in ['system_admin', 'user_admin'])
        
        # For update, delete - ONLY admins can modify (personnel cannot change anything)
        return bool(
            request.user.is_superuser or 
            request.user.role in ['system_admin', 'user_admin']
        )

class CanAccessUserDetail(permissions.BasePermission):
    """
    Permission for user detail views - users can see own data, admins see all
    """
    def has_object_permission(self, request, view, obj):
        return (obj == request.user or 
                request.user.is_superuser or
                request.user.role in ['system_admin', 'user_admin'])