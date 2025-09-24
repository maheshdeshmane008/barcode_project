from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_and_form_handler, name='assignrole'),
    path('get_permissions/<int:role_id>/', views.get_permissions, name='get_permissions'),
   
]
