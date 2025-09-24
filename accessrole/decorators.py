from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from assignrole.models import Assignrole # Import your Assignrole model
from user.models import CustomUser
from accessrole.models import AccessRole


def get_user_permissions(user):
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
        try:
            # Assuming 'accessrole' page has a page_id of 1 in your Assignrole table.
            # You should adjust this dynamically if you have more pages.
            permissions_obj = Assignrole.objects.get(role_id=user.role_id, page_id=1)
            user_permissions['can_view'] = permissions_obj.view
            user_permissions['can_insert'] = permissions_obj.insert
            user_permissions['can_update'] = permissions_obj.update
            user_permissions['can_delete'] = permissions_obj.delete
        except Assignrole.DoesNotExist:
            pass

    return user_permissions