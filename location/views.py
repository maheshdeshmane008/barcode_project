from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Location
from django.http import JsonResponse
from django import forms
from django.db.models import Q
import datetime
from .decorators import  get_user_permissions

# Define the form for server-side validation
class LocationForm(forms.Form):
    location = forms.CharField(required=True, max_length=255)
    upload_path = forms.CharField(required=True, max_length=512)
    print_path = forms.CharField(required=True, max_length=512)
    download_path = forms.CharField(required=True, max_length=512)

@login_required(login_url='authentication/login')
def index_and_form_handler(request): 
    user = request.user 
    user_permissions = get_user_permissions(user)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
       
            form = LocationForm(request.POST)        
            if form.is_valid():
                location_id = request.POST.get('location_id')
                location_name = form.cleaned_data['location']
                upload_path = form.cleaned_data['upload_path']
                print_path = form.cleaned_data['print_path']
                download_path = form.cleaned_data['download_path']
                date = datetime.datetime.now().date()

                # Check for unique location name, excluding the current object if editing
                queryset = Location.objects.filter(name=location_name)
                if location_id:
                    queryset = queryset.exclude(pk=location_id)
                
                if queryset.exists():
                    return JsonResponse({'success': False, 'errors': {'location': ["This location name already exists."]}})
                
                try:
                    if location_id:
                        if not user_permissions['can_update']:
                             return JsonResponse({'success': False, 'errors': {'general': ['You do not have permission to update.']}}, status=403)
                        # Edit existing location
                        location_obj = get_object_or_404(Location, pk=location_id)
                        location_obj.name = location_name
                        location_obj.upload_path = upload_path
                        location_obj.print_path = print_path
                        location_obj.download_path = download_path
                        location_obj.updated_by = request.user
                        location_obj.save()
                        message = 'Location updated successfully.'
                    else:
                        if not user_permissions['can_insert']:
                             return JsonResponse({'success': False, 'errors': {'general': ['You do not have permission to add.']}}, status=403)
                        # Add new location
                        Location.objects.create(
                            name=location_name,
                            upload_path=upload_path,
                            print_path=print_path,
                            download_path=download_path,
                            created_by=request.user,
                            updated_by=request.user,
                            date=date
                        )
                        message = 'Location added successfully.'
                    
                    return JsonResponse({'success': True, 'message': message})
                except Exception as e:
                    return JsonResponse({'success': False, 'errors': {'general': [str(e)]}})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
       
    if user_permissions['can_view']:
        # For GET request, render the page with existing data
        location = Location.objects.all().order_by('-date')
        context = {
            'location': location,
            'permissions': user_permissions,
        }
        return render(request, 'Location/index.html', context)
    else:      
        return redirect('unautorized')

@login_required(login_url='authentication/login')
def delete_location(request, id):
    user = request.user
    user_permissions = get_user_permissions(user)
    if user_permissions['can_delete']:
        try:
            location = get_object_or_404(Location, pk=id)
            location.status = '0' # Set status to '0' for soft delete
            location.updated_by = request.user
            location.save()
            messages.success(request, 'Location has been deleted.')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')        
        return redirect('location')
    else:
         return redirect('unautorized')
