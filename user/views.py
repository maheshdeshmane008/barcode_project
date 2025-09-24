import json
import datetime
import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import CustomUser, AccessRole, Location
from django.http import JsonResponse
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from .decorators import  get_user_permissions # Import the new functions


def send_welcome_email(user_email, user_name, password):
    """
    Sends a welcome email to the new user with their generated password.
    """
    subject = 'Welcome to the Barcode App!'
    message = f"""
Hello {user_name},

Your account has been successfully created.
Your username is your email address: {user_email}
Your temporary password is: {password}

Please log in and change your password as soon as possible.
Thank you!
"""
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

@login_required(login_url='authentication/login')
def index_and_form_handler(request):
    """
    Handles displaying the form and processing the form submission for user creation and updates.
    """
    user = request.user 
    user_permissions = get_user_permissions(user)
    if request.method == 'POST':
        try:
            # Check if the request is an AJAX request
            if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)
           
            # Get data from the POST request
            user_id = request.POST.get('location_id')
            location = request.POST.get('location')
            role = request.POST.get('role')
            name = request.POST.get('name')
            email = request.POST.get('email')

            # Server-side validation
            errors = {}
            if not location:
                errors['location'] = ['Please Select Location']
            if not role:
                errors['role'] = ['Please Select Access Role']
            if not name:
                errors['name'] = ['Please Enter User Name']
            if not email:
                errors['email'] = ['Please Enter User Email']
            
            # Check for existing email address
            if not user_id:  # This is a new user
                if CustomUser.objects.filter(email=email).exists():
                    errors['email'] = ['This email is already registered.']
            else:  # This is an update
                if CustomUser.objects.filter(email=email).exclude(pk=user_id).exists():
                    errors['email'] = ['This email is already registered to another user.']

            if errors:
                return JsonResponse({'success': False, 'errors': errors})
            
            # Handle database operations within a transaction
            with transaction.atomic():
                if user_id:
                    if not user_permissions['can_update']:
                             return JsonResponse({'success': False, 'errors': {'general': ['You do not have permission to update.']}}, status=403)
                        
                    # Update existing user
                    user = CustomUser.objects.get(pk=user_id)
                    user.location_id = Location.objects.get(pk=location)
                    user.role_id = AccessRole.objects.get(pk=role)
                    user.name = name
                    user.email = email
                    user.updated_by = request.user
                    user.save()
                    message = 'User updated successfully.'
                else:
                    if not user_permissions['can_insert']:
                             return JsonResponse({'success': False, 'errors': {'general': ['You do not have permission to add.']}}, status=403)
                        
                    # Create new user
                    # Generate a secure, temporary password
                    generated_password = secrets.token_urlsafe(12)
                    
                    user = CustomUser.objects.create(
                        location_id=Location.objects.get(pk=location),
                        role_id=AccessRole.objects.get(pk=role),
                        name=name,
                        email=email,
                        status=1,
                        password=make_password(generated_password), # Hash the password before saving
                        created_by=request.user,
                        updated_by=request.user
                    )
                    
                    # Send a welcome email to the newly created user with the plain-text password
                    send_welcome_email(user.email, user.name, generated_password)
                    message = 'User added successfully.'

            return JsonResponse({'success': True, 'message': message})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
        
    if user_permissions['can_view']:
        # Handle GET request to display the form and user list
        access = AccessRole.objects.filter(status=1).order_by('-date')
        location = Location.objects.filter(status=1).order_by('-date')
        user = CustomUser.objects.filter(status=1,is_superuser=0).order_by('-date_joined')
        context = {
            'access': access,
            'location': location,
            'user': user,
            'permissions': user_permissions,
        }
        return render(request, 'user/index.html', context)
    else:      
        return redirect('unautorized')
    
@login_required(login_url='authentication/login')
def user_delete(request, user_id):
    """
    Handles user soft deletion by updating the is_active status to False.
    """
    user = request.user
    user_permissions = get_user_permissions(user)
    if user_permissions['can_delete']:
        try:
            user_to_deactivate = get_object_or_404(CustomUser, pk=user_id)
            user_to_deactivate.status = 0
            user_to_deactivate.save()
            messages.success(request, f'User {user_to_deactivate.name} has been deactivated successfully.')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')        
        return redirect('user')
    else:
         return redirect('unautorized')