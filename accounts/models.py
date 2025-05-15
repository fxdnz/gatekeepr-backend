from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class UserAccountManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not name:
            raise ValueError('Users must have a name')
        if not password:
            raise ValueError('Users must have a password')
        
        email = self.normalize_email(email)
        user = self.model(email=email, name=name)
        user.set_password(password)
        user.is_active = False
        user.is_staff = True  # all users are staff-level
        user.role = 'staff'
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, name, password):
        user = self.create_user(email=email, name=name, password=password)
        user.is_active = True
        user.is_superuser = True
        user.role = 'admin'
        user.save(using=self._db)
        return user

class UserAccount(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    )

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)  # every user is staff
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserAccountManager()

    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.name

    def __str__(self):
        return f"{self.email} ({self.role})"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
