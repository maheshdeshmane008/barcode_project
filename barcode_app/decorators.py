from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from assignrole.models import Assignrole # Import your Assignrole model
# Centralized mapping of page names to their corresponding page_id
PAGE_ID_MAP = {
    "upload": 5,
    "download": 6,
    "exception": 7,
    # Add more pages here as needed
}
def get_user_permissions(user,page):
    """
    Retrieves and caches user permissions.
    """
    user_permissions = {
        'can_view': False,
        'can_insert': False,
        'can_update': False,
        'can_delete': False,
    }

    if user.is_superuser:
        for perm in user_permissions:
            user_permissions[perm] = True
    else:
      
            page_id = PAGE_ID_MAP.get(page)
            if page_id is not None:
                try:
                    permissions_obj = Assignrole.objects.get(role_id=user.role_id, page_id=page_id)
                    user_permissions['can_view'] = permissions_obj.view
                    user_permissions['can_insert'] = permissions_obj.insert
                    user_permissions['can_update'] = permissions_obj.update
                    user_permissions['can_delete'] = permissions_obj.delete
                except Assignrole.DoesNotExist:
                    pass

    return user_permissions