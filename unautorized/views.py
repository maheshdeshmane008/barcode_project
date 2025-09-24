from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required(login_url='authentication/login')
def index(request): 
    
    return render(request, 'unauthorized/index.html')


