from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import UserAccount


@receiver(post_save, sender=UserAccount)
def handle_user_emails(sender, instance, created, **kwargs):
    # (1) When a new user is created
    if created and not instance.is_superuser:
        # Email to admin
        admin_login_url = 'http://localhost:8000/admin'
        send_mail(
            subject='New User Registration - Approval Needed',
            message=(
                f'User {instance.email} has registered and is pending activation.\n\n'
                f'Click here to review and approve them:\n{admin_login_url}'
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['gatekeepr.noreply@gmail.com'],
            fail_silently=False,
        )

        # Email to user: "Please wait for approval"
        send_mail(
            subject='Thanks for Registering — Awaiting Approval',
            message=(
                f"Hi {instance.name},\n\n"
                f"Thanks for signing up at Gatekeepr!\n"
                f"Your account is pending admin approval.\n"
                f"You will receive another email once your account is activated.\n\n"
                f"— The Gatekeepr Team"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[instance.email],
            fail_silently=False,
        )

