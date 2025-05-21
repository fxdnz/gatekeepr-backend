from djoser.email import ActivationEmail, PasswordResetEmail
from django.core.mail import EmailMultiAlternatives

class CustomActivationEmail(ActivationEmail):
    def get_context_data(self):
        context = super().get_context_data()
        context['url'] = f"https://gatekeepr1.netlify.app/activate/{context['uid']}/{context['token']}"
        return context

    def send(self, to, *args, **kwargs):
        context = self.get_context_data()
        subject = "Activate your Gatekeepr account"
        body = (
            f"Hi {context['user'].get_full_name()},\n\n"
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
        context['url'] = f"https://gatekeepr1.netlify.app/password/reset/confirm/{context['uid']}/{context['token']}"
        return context

    def send(self, to, *args, **kwargs):
        context = self.get_context_data()
        subject = "Reset your Gatekeepr password"
        body = (
            f"Hi {context['user'].get_full_name()},\n\n"
            f"You requested a password reset. Click the link below to set a new password:\n\n"
            f"{context['url']}\n\n"
            f"If you didn’t request this, you can safely ignore this email.\n\n"
            f"— The Gatekeepr Team"
        )
        msg = EmailMultiAlternatives(subject, body, self.from_email, [to])
        msg.send()