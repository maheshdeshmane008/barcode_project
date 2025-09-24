from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AccessRole
from assignrole.models import Assignrole 
from django.http import JsonResponse
from django import forms
from django.db.models import Q
import datetime
from .decorators import  get_user_permissions # Import the new functions

# Define the form for server-side validation
class LocationForm(forms.Form):
    accessrole = forms.CharField(required=True, max_length=255)

@login_required(login_url='authentication/login')
def index_and_form_handler(request):
    user = request.user 
    user_permissions = get_user_permissions(user)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
        if user_permissions['can_update']:
            form = LocationForm(request.POST)
            
            if form.is_valid():
                accessrole =form.cleaned_data['accessrole']
                accessrole_id = request.POST.get('accessrole_id')
                date = datetime.datetime.now().date()

                # Check for unique location name, excluding the current object if editing
                queryset = AccessRole.objects.filter(name=accessrole)
                if accessrole_id:
                    queryset = queryset.exclude(pk=accessrole_id)
                
                if queryset.exists():
                    return JsonResponse({'success': False, 'errors': {'accessrole': ["This Access Role  already exists."]}})
                
                try:
                    if accessrole_id:
                        if not user_permissions['can_update']:
                             return JsonResponse({'success': False, 'errors': {'general': ['You do not have permission to update.']}}, status=403)
                        # Edit existing location
                        accessrole_obj = get_object_or_404(AccessRole, pk=accessrole_id)
                        accessrole_obj.name = accessrole                   
                        accessrole_obj.updated_by = request.user
                        accessrole_obj.save()
                        message = 'Access Role updated successfully.'
                    else:
                        if not user_permissions['can_insert']:
                             return JsonResponse({'success': False, 'errors': {'general': ['You do not have permission to add.']}}, status=403)
                        # Add new location
                        AccessRole.objects.create(
                            name=accessrole,
                            status='1',
                            created_by=request.user,
                            updated_by=request.user,
                            date=date
                        )
                        message = 'Access Role added successfully.'
                    
                    return JsonResponse({'success': True, 'message': message})
                except Exception as e:
                    return JsonResponse({'success': False, 'errors': {'general': [str(e)]}})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        else:
            return redirect('unautorized')

    # For GET request, render the page with existing data
  
    if user_permissions['can_view']:
            access =  AccessRole.objects.filter(status=1).order_by('-date')
            context = {
                'access': access,
                'permissions': user_permissions,
            }
            return render(request, 'accessrole/index.html', context)
    else:      
        return redirect('unautorized')

@login_required(login_url='authentication/login')
def delete_accessrole(request, id):
    user = request.user
    user_permissions = get_user_permissions(user)
    if user_permissions['can_delete']:
        try:
            access = get_object_or_404(AccessRole, pk=id)
            access.status = '0' # Set status to '0' for soft delete
            access.updated_by = request.user
            access.save()
            messages.success(request, 'Access Role has been deleted.')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')        
        return redirect('accessrole')
    else:
         return redirect('unautorized')
