from djoser.email import ActivationEmail, PasswordResetEmail
from django.core.mail import EmailMultiAlternatives


class CustomActivationEmail(ActivationEmail):
    def send(self, to, *args, **kwargs):
        uid = self.context['uid']
        token = self.context['token']
        activation_url = f"https://gatekeepr1.netlify.app/activate/{uid}/{token}"

        subject = "Activate your Gatekeepr account"
        body = (
            f"Hi {self.context['user'].get_full_name()},\n\n"
            f"Thanks for signing up!\n"
            f"Please activate your account by clicking the link below:\n\n"
            f"{activation_url}\n\n"
            f"— The Gatekeepr Team"
        )
        msg = EmailMultiAlternatives(subject, body, self.from_email, [to])
        msg.send()


class CustomPasswordResetEmail(PasswordResetEmail):
    def send(self, to, *args, **kwargs):
        uid = self.context['uid']
        token = self.context['token']
        reset_url = f"https://gatekeepr1.netlify.app/password/reset/confirm/{uid}/{token}"

        subject = "Reset your Gatekeepr password"
        body = (
            f"Hi {self.context['user'].get_full_name()},\n\n"
            f"You requested a password reset. Click the link below to set a new password:\n\n"
            f"{reset_url}\n\n"
            f"If you didn’t request this, you can ignore this email.\n\n"
            f"— The Gatekeepr Team"
        )
        msg = EmailMultiAlternatives(subject, body, self.from_email, [to])
        msg.send()
