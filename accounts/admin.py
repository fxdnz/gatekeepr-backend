from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import UserAccount

@admin.action(description='Approve selected users')
def approve_users(modeladmin, request, queryset):
    queryset.update(is_active=True)

class UserAccountAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'role', 'is_active', 'is_staff')
    list_filter = ('is_active', 'role')
    search_fields = ('email', 'name')
    ordering = ('email',)
    actions = [approve_users]  # 👈 Add your custom action here

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(UserAccount, UserAccountAdmin)
