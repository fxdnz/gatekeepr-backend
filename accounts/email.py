from djoser.email import ActivationEmail, PasswordResetEmail
from django.core.mail import EmailMultiAlternatives

class CustomActivationEmail(ActivationEmail):
    def get_context_data(self):
        context = super().get_context_data()
        # Set the full frontend URL
        context['url'] = f"https://gatekeepr1.netlify.app/activate/{context['uid']}/{context['token']}"
        # Explicitly disable domain and protocol to prevent prepending
        context['domain'] = ''
        context['protocol'] = ''
        context['site_name'] = 'Gatekeepr'
        return context

    def send(self, to, *args, **kwargs):
        context = self.get_context_data()
        subject = "Activate your Gatekeepr account"
        body = (
            f"Hi {context['user'].get_full_name() or context['user'].username},\n\n"
            f"Thanks for signing up!\n"
            f"Please activate your account by clicking the link below:\n\n"
            f"{context['url']}\n\n"
            f"— The Gatekeepr Team"
        )
        msg = EmailMultiAlternatives(subject, body, self.from_email, [to])
        msg.send()

class CustomPasswordResetEmail(PasswordResetEmail):
    def get_context_data(self):
        context = super().get_context_data()
        # Set the full frontend URL
        context['url'] = f"https://gatekeepr1.netlify.app/password/reset/confirm/{context['uid']}/{context['token']}"
        # Explicitly disable domain and protocol to prevent prepending
        context['domain'] = ''
        context['protocol'] = ''
        context['site_name'] = 'Gatekeepr'
        return context

    def send(self, to, *args, **kwargs):
        context = self.get_context_data()
        subject = "Reset your Gatekeepr password"
        body = (
            f"Hi {context['user'].get_full_name() or context['user'].username},\n\n"
            f"You requested a password reset. Click the link below to set a new password:\n\n"
            f"{context['url']}\n\n"
            f"If you didn’t request this, you can safely ignore this email.\n\n"
            f"— The Gatekeepr Team"
        )
        msg = EmailMultiAlternatives(subject, body, self.from_email, [to])
        msg.send()