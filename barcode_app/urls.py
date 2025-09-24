from django.urls import path
from . import views

urlpatterns = [
    # path('upload/', views.upload_pdf, name='upload_pdf'),
    # path('results/', views.results_view, name='results_view'),
    
    
    # # New URL for the search page
    # path('search/', views.search_barcode_view, name='search_barcode_view'),
    # # New API endpoint for searching
     
    path('uploadlabel/', views.index, name='barcode'),
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('download/', views.download_pdf, name='download_pdf'),
    path('search-barcode/', views.search_barcode_api, name='search-barcode'),
    path('update-selected-print-status/', views.update_selected_print_status, name='update-selected-print-status'),
    path('print-labels/', views.print_labels, name='print-labels'),
    path('update-print-status/', views.update_print_status, name='update-print-status'),
    path('exception/', views.exception, name='exception'),
    path('search-exceptions/', views.search_exceptions, name='search_exceptions'),
    path('get-label/<int:label_id>/', views.get_shipping_label, name='get-shipping-label'),

     

]