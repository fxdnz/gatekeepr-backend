from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers
from .models import UserAccount
from .signals import send_credentials_email  # Import the email function

class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users - includes all user fields
    """
    class Meta:
        model = UserAccount
        fields = ('id', 'email', 'name', 'role', 'is_active', 'is_staff', 'date_joined', 'last_login')
        read_only_fields = fields

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = UserAccount
        fields = ('id', 'email', 'name', 'password', 'role')
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        current_user = request.user
        
        # Only allow superusers or admin roles to create users
        if not (current_user.is_superuser or 
                current_user.role in ['system_admin', 'user_admin']):
            raise serializers.ValidationError("Only administrators can create user accounts.")
        
        print(f"Admin creating user account via API: {current_user.email}")
        
        # Extract password before creating user
        password = validated_data.get('password')
        
        # Create user
        user = UserAccount.objects.create_user(**validated_data)
        
        # Send credentials email
        if password:
            send_credentials_email(user, password)
            print(f"DEBUG: Credentials email sent to {user.email}")
        else:
            print(f"DEBUG: User created but no password provided for email")
            
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for users to view their own profile (READ-ONLY)
    """
    class Meta:
        model = UserAccount
        fields = ('id', 'email', 'name', 'role', 'date_joined')
        read_only_fields = ('id', 'email', 'name', 'role', 'date_joined')

class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for admins to update any user (EXCLUDES PASSWORD)
    """
    class Meta:
        model = UserAccount
        fields = ('id', 'email', 'name', 'role', 'is_active')
        read_only_fields = ('email',)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.role = validated_data.get('role', instance.role)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance