from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from cloudinary.models import CloudinaryField

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        user = self.create_user(email, name, password)
        user.is_staff = True
        user.is_superuser = True
        user.role = 'admin'
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('user', 'User'), ('admin', 'Admin')]
    name       = models.CharField(max_length=100)
    email      = models.EmailField(unique=True)
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']
    objects = UserManager()

    def __str__(self):
        return self.name

class SnackItem(models.Model):
    name       = models.CharField(max_length=100)
    price      = models.DecimalField(max_digits=8, decimal_places=2)
    is_active  = models.BooleanField(default=True)
    image      = CloudinaryField('image', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class Order(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    date       = models.DateField()
    is_locked  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.name} - {self.date}"


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    snack    = models.ForeignKey(SnackItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.snack.name} x{self.quantity}"        