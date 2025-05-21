from django.contrib.auth.tokens import default_token_generator
from django.conf import settings as django_settings

from djoser.email import ActivationEmail, PasswordResetEmail, ConfirmationEmail, PasswordChangedConfirmationEmail
from djoser import utils
from djoser.conf import settings

class CustomActivationEmail(ActivationEmail):
    template_name = "email/activation.html"

    def get_context_data(self):
        # ActivationEmail can be deleted
        context = super().get_context_data()

        user = context.get("user")
        context["frontend_url"] = django_settings.FRONTEND_URL
        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["url"] = settings.ACTIVATION_URL.format(**context)
        return context

class CustomPasswordResetEmail(PasswordResetEmail):
    template_name = "email/password_reset.html"

    def get_context_data(self):
        # PasswordResetEmail can be deleted
        context = super().get_context_data()

        user = context.get("user")
        context["frontend_url"] = django_settings.FRONTEND_URL
        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["url"] = settings.PASSWORD_RESET_CONFIRM_URL.format(**context)
        return context

class CustomConfirmationEmail(ConfirmationEmail):
    template_name = "email/confirmation.html"

    def get_context_data(self):
        # ActivationEmail can be deleted
        context = super().get_context_data()

        context["frontend_url"] = django_settings.FRONTEND_URL
        return context

class CustomPasswordChangedConfirmationEmail(PasswordChangedConfirmationEmail):
    template_name = "email/password_changed_confirmation.html"

    def get_context_data(self):
        # ActivationEmail can be deleted
        context = super().get_context_data()

        context["frontend_url"] = django_settings.FRONTEND_URL
        return context