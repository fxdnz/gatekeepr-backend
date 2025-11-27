from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from .models import UserAccount

def send_credentials_email(user, password):
    """Send dark theme login credentials to user"""
    try:
        subject = 'Your Gatekeepr Account is Ready'
        
        # Context for the template
        context = {
            'user': user,
            'password': password,
            'frontend_url': settings.FRONTEND_URL,
            'login_url': f"{settings.FRONTEND_URL}/login",
        }
        
        # Render HTML template
        html_content = render_to_string('email/credentials.html', context)
        
        # Create plain text version
        text_content = f"""
Welcome to Gatekeepr, {user.name}!

Your account has been created successfully.

LOGIN CREDENTIALS:
Email: {user.email}
Password: {password}

Login URL: {settings.FRONTEND_URL}

SECURITY: Please change your password after first login.

Need help? Contact your administrator.

— Gatekeepr Team
"""
        
        # Send both HTML and plain text versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"DEBUG: Credentials email sent to {user.email}")
        return True
        
    except Exception as e:
        print(f"DEBUG: Error sending credentials email: {e}")
        return False

# Optional: Keep this signal only for logging, not for email sending
@receiver(post_save, sender=UserAccount)
def handle_user_creation(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        print(f"DEBUG: User {instance.email} created - is_active: {instance.is_active}")
        # No automatic email sending - controlled by admin