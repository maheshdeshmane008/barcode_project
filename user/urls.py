from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_and_form_handler, name='user'),
    #This URL handles the deletion of a location by its ID.
   path('user/delete/<int:user_id>/', views.user_delete, name='user-delete'),
]
