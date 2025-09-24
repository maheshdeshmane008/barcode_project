from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_and_form_handler, name='accessrole'),
    #This URL handles the deletion of a location by its ID.
    path('accessrole/delete/<int:id>/', views.delete_accessrole, name='access-delete'),
]
