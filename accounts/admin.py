from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .models import UserAccount
from .signals import send_credentials_email

class UserCreationForm(forms.ModelForm):
    """A form for creating new users with password generation button"""
    
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            'placeholder': _('Generate or enter password')
        }),
        required=True,
        help_text=_("Password will be sent to the user via email")
    )
    
    class Meta:
        model = UserAccount
        fields = ('email', 'name', 'role', 'password', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].initial = True

    def save(self, commit=True):
        user = super().save(commit=False)
        
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
            
        if commit:
            user.save()
        return user

class UserAccountAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    list_display = ('email', 'name', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'role', 'is_staff', 'is_superuser')
    search_fields = ('email', 'name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password', 'is_active'),
        }),
    )
    
    def has_add_permission(self, request):
        """Allow superusers OR admin roles"""
        return (request.user.is_superuser or 
                request.user.role in ['system_admin', 'user_admin'])
    
    def has_change_permission(self, request, obj=None):
        """Allow superusers OR admin roles"""
        return (request.user.is_superuser or 
                request.user.role in ['system_admin', 'user_admin'])
    
    def has_delete_permission(self, request, obj=None):
        """Allow superusers OR admin roles"""
        return (request.user.is_superuser or 
                request.user.role in ['system_admin', 'user_admin'])
    
    def save_model(self, request, obj, form, change):
        # Get the password before saving
        password = form.cleaned_data.get('password')
        
        # Check if this is a new user creation (not change)
        is_new_user = not change
        
        # Save the user first
        super().save_model(request, obj, form, change)
        
        # Send email only for new users with a password
        if is_new_user and password:
            success = send_credentials_email(obj, password)
            
            if success:
                messages.success(
                    request,
                    f'User {obj.email} created successfully. Credentials email sent.'
                )
            else:
                messages.warning(
                    request,
                    f'User {obj.email} created, but failed to send credentials email.'
                )
        elif is_new_user and not password:
            messages.warning(
                request,
                f'User {obj.email} created, but no password was set.'
            )

admin.site.register(UserAccount, UserAccountAdmin)