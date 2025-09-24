# authenticationapp/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password, status=1)
        if email and password:
            if user is not None:
                login(request, user)
                request.session['id'] = user.id
                request.session['first_name'] = user.name
                request.session['role'] = user.role_id_id
                messages.success(request, f"Welcome back, {email}!")
                return redirect('accessrole')  # Make sure this URL is correctly configured
            else:
                messages.error(
                request, 'Invalid credentials,try again')
                return render(request, 'authentication/login.html')
            
        messages.error(
        request, 'Please fill all fields')
        return render(request, 'authentication/login.html')
            
    return render(request, 'authentication/login.html')

def logout_view(request): 
    logout(request)       
    return redirect('login')