from djoser.email import ActivationEmail, PasswordResetEmail

class CustomActivationEmail(ActivationEmail):
    def get_context_data(self):
        context = super().get_context_data()
        uid = context['uid']
        token = context['token']
        context['url'] = f"https://gatekeepr1.netlify.app/activate/{uid}/{token}"
        return context

class CustomPasswordResetEmail(PasswordResetEmail):
    def get_context_data(self):
        context = super().get_context_data()
        uid = context['uid']
        token = context['token']
        context['url'] = f"https://gatekeepr1.netlify.app/password/reset/confirm/{uid}/{token}"
        return context
