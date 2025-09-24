# barcode_app/models.py
from django.db import models
from user.models import CustomUser 
from location.models import Location 
from django.utils import timezone
class ShippingLabelData(models.Model):
    # Add choices for the print status
    PRINT_STATUS_CHOICES = [
        (0, 'New / Unprinted'),
        (1, 'Printed / Successfully Processed'),
        (2, 'Sent for Printing')
    ]
    location = models.ForeignKey(Location, related_name='shipping_location', on_delete=models.SET_NULL, null=True) 
    user = models.ForeignKey(CustomUser, related_name='shipping_user', on_delete=models.SET_NULL, null=True) 
    path = models.FileField(upload_to='pdfs/')
  
    status = models.IntegerField(default=0)
    print_download_status = models.IntegerField(
        choices=PRINT_STATUS_CHOICES, 
        default=1,
        verbose_name="Print Status"
    )
    created_by = models.ForeignKey(CustomUser, related_name='labels_created', on_delete=models.SET_NULL, null=True)
    updated_by = models.CharField(max_length=50, default='active')
  
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Add this line without a default value
    upload_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Label: {self.path.name}"
    
class ScannedBarcode(models.Model):
    shipping_label = models.ForeignKey(ShippingLabelData, related_name='barcodes', on_delete=models.CASCADE)
    barcode_value = models.CharField(max_length=255)
    created_by = models.ForeignKey(CustomUser, related_name='barcodes_created', on_delete=models.SET_NULL, null=True)
  
    created_at = models.DateTimeField(auto_now=True)   
    scanned_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.barcode_value

class DuplicateBarcodeException(models.Model):
    file_name = models.CharField(max_length=255)
    duplicate_barcode = models.CharField(max_length=255)
    location = models.ForeignKey(Location, related_name='Duplicate_location', on_delete=models.SET_NULL, null=True)  
    upload_date = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, related_name='exceptions_created', on_delete=models.SET_NULL, null=True)  
 
    created_at = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"Duplicate: {self.duplicate_barcode} in {self.file_name}"