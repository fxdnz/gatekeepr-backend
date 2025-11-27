from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet as DjoserUserViewSet
from .models import UserAccount
from .signals import send_credentials_email
from .permissions import CanManageUsers

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageUsers])
def admin_create_user(request):
    """
    Only system_admin and user_admin can create user accounts via this endpoint
    """
    viewset = DjoserUserViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    # Create the user
    response = viewset.create(request)
    
    # If creation was successful, send credentials email
    if response.status_code == status.HTTP_201_CREATED:
        try:
            # Extract user data from response
            user_data = response.data
            user = UserAccount.objects.get(email=user_data['email'])
            
            # Send credentials email
            password = request.data.get('password')
            if password:
                send_credentials_email(user, password)
                
        except Exception as e:
            print(f"DEBUG: Error in admin_create_user: {e}")
    
    return response