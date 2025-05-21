from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import UserAccount

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = UserAccount
        fields = ('id', 'email', 'name', 'password')

    def create(self, validated_data):
        print("Custom serializer create method triggered")  # <-- This should show up in the terminal
        user = super().create(validated_data)
        admin_login_url = 'https//gatekeepr-backend.onrender.com/admin/'

        send_mail(
            subject='New User Registration - Approval Needed',
            message=(
                f'User {user.email} has registered and is pending activation.\n\n'
                f'Click here to review and approve them:\n{admin_login_url}'
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['gatekeepr.noreply@gmail.com'],  # <-- Use a valid admin email here
            fail_silently=False,
        )
        return user
