from django.db import models
from django.conf import settings

class AccessRole(models.Model):
    # Primary Key
    id = models.AutoField(primary_key=True)
    
    # Location name
    name = models.CharField(max_length=255, unique=True, verbose_name="Access Role Name")
    
    
    # Status (e.g., active, inactive, pending)
    status = models.CharField(max_length=50, default='active')
    
    # Date field
    date = models.DateField(auto_now_add=True)
    
    # Audit fields for user tracking
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='accessrole_created', on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='accessrole_updated', on_delete=models.SET_NULL, null=True)
   
    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """String representation of the accessrole object."""
        return self.name

    class Meta:
        verbose_name = "Access Role"
        verbose_name_plural = "Access Roles"
        ordering = ['created_at']
