from django.db import models
from accessrole.models import AccessRole 
from django.conf import settings
class Pagelist(models.Model):
    # Primary Key
    id = models.AutoField(primary_key=True)
    
    # display_name name
    display_name = models.CharField(max_length=255, unique=True, verbose_name="Page Name")
    module_name = models.CharField(max_length=255, verbose_name="Module Name") 

    # Status (e.g., active, inactive, pending)
    status = models.BooleanField(default=True) 

    def __str__(self):
        """String representation of the accessrole object."""
        return self.display_name

    class Meta:
        verbose_name = "Page List"
        verbose_name_plural = "Page Lists"
        ordering = ['id']

class Assignrole(models.Model):
    # Primary Key
    id = models.AutoField(primary_key=True)
    
    # Location name
    page = models.ForeignKey(Pagelist, related_name='assigned_pages', on_delete=models.SET_NULL, null=True) 
    role_id = models.ForeignKey(AccessRole, related_name='assigned_roles', on_delete=models.SET_NULL, null=True)    
    
    view = models.BooleanField(default=False, help_text="Permission to view this page.")
    insert = models.BooleanField(default=False, help_text="Permission to add new data.")
    update = models.BooleanField(default=False, help_text="Permission to update existing data.")
    delete = models.BooleanField(default=False, help_text="Permission to delete data.")
    
    # Date field
    date = models.DateField(auto_now_add=True)
    
    # Audit fields for user tracking
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assign_roles_created', on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assign_roles_updated', on_delete=models.SET_NULL, null=True)
  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    
    class Meta:
        verbose_name = "Assigned Role"
        verbose_name_plural = "Assigned Roles"
        ordering = ['-date']

    def __str__(self):
        """String representation of the Assigned Role object."""
        return f"Role for {self.page.display_name}"
