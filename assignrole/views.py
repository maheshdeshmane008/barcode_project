from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AccessRole,Pagelist,Assignrole
from django.http import JsonResponse
from django import forms
from django.db.models import Q
import json
import datetime
from django.db import transaction
from .decorators import  get_user_permissions
# Define the form for server-side validation
class LocationForm(forms.Form):
    accessrole = forms.CharField(required=True, max_length=255)

@login_required(login_url='authentication/login')
def index_and_form_handler(request):
    """
    Handles displaying the form and processing the form submission for assigning roles.
    """
    user = request.user 
    user_permissions = get_user_permissions(user)
    if user_permissions['can_update']:
        if request.method == 'POST':
            try:
                # Check if the request is an AJAX request
                if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

                # Parse JSON data sent from the frontend
                data = json.loads(request.body)
                access_role_id = data.get('access_role_id')
                assigned_pages = data.get('assigned_pages', [])

                if not access_role_id:
                    return JsonResponse({'success': False, 'errors': {'type': ['Please select an Access Role.']}}, status=400)
                
                try:
                    access_role = AccessRole.objects.get(pk=access_role_id)
                except AccessRole.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Access Role not found.'}, status=404)

                # Use a transaction to ensure all database operations are atomic.
                with transaction.atomic():
                    # Delete existing role assignments for this access role to handle edits.
                    # We use 'role_id' to explicitly filter by the foreign key's primary key.
                    Assignrole.objects.filter(role_id=access_role_id).delete()

                    # Loop through the submitted data and create new Assignrole objects
                    for page_data in assigned_pages:
                        page_id = page_data.get('page_id')
                        view_perm = page_data.get('view', False)
                        insert_perm = page_data.get('insert', False)
                        update_perm = page_data.get('update', False)
                        delete_perm = page_data.get('delete', False)
                        
                        if any([view_perm, insert_perm, update_perm, delete_perm]):
                            # Only create an entry if at least one permission is checked
                            try:
                                page = Pagelist.objects.get(pk=page_id)
                                Assignrole.objects.create(
                                    role_id=access_role,
                                    page=page,
                                    view=view_perm,
                                    insert=insert_perm,
                                    update=update_perm,
                                    delete=delete_perm,
                                    created_by=request.user,
                                    updated_by=request.user,
                                )
                            except Pagelist.DoesNotExist:
                                # Log an error or return a specific response if the page doesn't exist
                                pass # Or handle error appropriately

                return JsonResponse({'success': True, 'message': 'Role assignments saved successfully.'})

            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)}, status=500)
    else:
        return redirect('unautorized')
    if user_permissions['can_view']:
        # Handle GET request to display the form
        access =  AccessRole.objects.filter(status=1).order_by('-date')
        pagelist =  Pagelist.objects.filter(status=1).order_by('id')
        context = {
            'access': access,
            'pagelist': pagelist,
            'permissions': user_permissions,
        }
        return render(request, 'assignrole/index.html', context)
    else:      
        return redirect('unautorized')

@login_required
def get_permissions(request, role_id):
    """
    Fetches existing permissions for a given access role.
    This view is called via AJAX when an access role is selected.
    """
    try:
        # Get all existing permissions for the selected role
        permissions = Assignrole.objects.filter(role_id=role_id)
        
        # Prepare data to be sent as JSON
        permissions_data = []
        for perm in permissions:
            permissions_data.append({
                'page_id': perm.page.id,
                'view': perm.view,
                'insert': perm.insert,
                'update': perm.update,
                'delete': perm.delete,
            })
            
        return JsonResponse({'success': True, 'permissions': permissions_data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
