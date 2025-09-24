from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_and_form_handler, name='location'),
    #This URL handles the deletion of a location by its ID.
    path('location/delete/<int:id>/', views.delete_location, name='location-delete'),
]
