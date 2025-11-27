from django.contrib.auth.tokens import default_token_generator
from django.conf import settings as django_settings
from djoser import utils
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class CustomPasswordResetEmail:
    def __init__(self, request, context):
        self.request = request
        self.context = context
        logger.info(f"PasswordResetEmail initialized with context: {context}")

    def get_context_data(self):
        context = self.context.copy()
        user = context.get("user")
        logger.info(f"Original context user: {user}")
        
        if user:
            context["frontend_url"] = django_settings.FRONTEND_URL
            context["uid"] = utils.encode_uid(user.pk)
            context["token"] = default_token_generator.make_token(user)
            # Ensure user object has required attributes
            context["user"] = user
            logger.info(f"Enhanced context: { {k: v for k, v in context.items() if k != 'user'} }")
        
        return context

    def send(self, to):
        try:
            context = self.get_context_data()
            logger.info(f"Sending email to: {to}")
            logger.info(f"Final context keys: {list(context.keys())}")
            
            subject = "Reset Your Gatekeepr Password"
            
            # Test template rendering
            html_content = render_to_string('email/password_reset.html', context)
            logger.info(f"HTML content length: {len(html_content)}")
            
            if len(html_content) < 100:
                logger.error("HTML template rendered empty or very short content!")
                
            # Create plain text fallback
            text_content = f"Password reset requested for {to[0]}"
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=django_settings.EMAIL_HOST_USER,
                to=to,
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            logger.info("Email sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise

class CustomPasswordChangedConfirmationEmail:
    def __init__(self, request, context):
        self.request = request
        self.context = context
        logger.info(f"PasswordChangedConfirmationEmail initialized with context: {context}")

    def get_context_data(self):
        context = self.context.copy()
        user = context.get("user")
        
        if user:
            context["frontend_url"] = django_settings.FRONTEND_URL
            context["current_date"] = timezone.now().strftime("%B %d, %Y at %H:%M %Z")
            context["user"] = user
        
        return context

    def send(self, to):
        try:
            context = self.get_context_data()
            logger.info(f"Sending confirmation email to: {to}")
            
            subject = "Your Gatekeepr Password Has Been Changed"
            
            html_content = render_to_string('email/password_changed_confirmation.html', context)
            logger.info(f"Confirmation HTML content length: {len(html_content)}")
            
            text_content = f"Password changed confirmation for {to[0]}"
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=django_settings.EMAIL_HOST_USER,
                to=to,
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            logger.info("Confirmation email sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending confirmation email: {str(e)}")
            raise