# barcode_app/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from accessrole.models import AccessRole 
from location.models import Location 
from authentication.models import CustomUserManager 


class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Primary Key
    id = models.AutoField(primary_key=True)
    role_id = models.ForeignKey(AccessRole, related_name='user_access_role', on_delete=models.SET_NULL, null=True) 
    location_id = models.ForeignKey(Location, related_name='user_location', on_delete=models.SET_NULL, null=True) 

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    
    # These are required fields for a user model.
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    
    # The 'status' field from your request, I'll assume it's a boolean.
    status=models.CharField(max_length=50, default='active')
    
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # These fields require a foreign key to the model itself, which is a bit
    # complex to set up directly in the initial model definition.
    # You will have to handle this with a more advanced approach,
    # possibly using a post_save signal or an abstract base model.
    created_by =models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_created'
    )
    updated_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_updated'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email