# barcode_app/views.py
import os
import json
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from .models import ShippingLabelData, ScannedBarcode, DuplicateBarcodeException,Location
from PIL import Image
from pyzbar.pyzbar import decode
import fitz
from django.conf import settings
from django.db import transaction
from datetime import datetime
from io import BytesIO
from django.db.models import Prefetch
from django.db.models.query import QuerySet
from .decorators import  get_user_permissions # Import the new functions

def index(request):
    user = request.user 
    user_permissions = get_user_permissions(user,'upload')
  
    if user_permissions['can_view']:
        upload_path = None
        user_instance = request.user if request.user.is_authenticated else None
        # Check if the user is logged in and has a location linked to their profile.
        if user.is_authenticated and user.location_id:
            try:
                # Assuming 'location_id' is the ForeignKey field on your CustomUser model
                location = Location.objects.get(id=user_instance.location_id.id)
                upload_path = location.upload_path
            except Location.DoesNotExist:
                pass # Handle case where location doesn't exist
        
            context = {               
                'permissions': user_permissions,
                'upload_path': upload_path
            }
            return render(request, 'barcode_app/index.html', context)
    else:      
        return redirect('unautorized')
  


def exception(request):
    
    user = request.user 
    user_permissions = get_user_permissions(user,'exception')
    if user_permissions['can_view']:
        
            context = {               
                'permissions': user_permissions
            }
            return render(request, 'barcode_app/exception.html', context)
    else:      
        return redirect('unautorized')

@csrf_exempt
def upload_pdf(request):
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('pdf_files')
        
        # Determine the user for logging purposes, handling anonymous users
      
        # Determine the user for logging purposes
        user_instance = request.user if request.user.is_authenticated else None
         # Check if the user is authenticated and has a location ID
        if user_instance and user_instance.location_id:
            user_location_id = user_instance.location_id.id
        else:
            # Handle cases where the user is not logged in or has no location
            # You might want to return an error or use a default value.
            return JsonResponse({'success': False, 'message': 'User has no location so kindly assign the location.'}, status=403)
        date_today = datetime.now().date()
        results = []
        
        current_year = datetime.now().year
        current_year_prefix = str(current_year)[-2:]
        previous_year_prefix = str(current_year - 1)[-2:]
        
        for file in uploaded_files:
            try:
                doc = fitz.open(stream=file.read(), filetype="pdf")
                found_barcodes = []
                for page in doc:
                    pix = page.get_pixmap(dpi=300) 
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    decoded_objects = decode(img)
                    for obj in decoded_objects:
                        barcode_value = obj.data.decode('utf-8')
                        if barcode_value.startswith(f'{current_year_prefix}-') or barcode_value.startswith(f'{previous_year_prefix}-'):
                            found_barcodes.append(barcode_value)
                doc.close()

                unique_found_barcodes = set(found_barcodes)

                if not unique_found_barcodes:
                    DuplicateBarcodeException.objects.create(
                        file_name=file.name,
                        location_id =user_location_id,
                        duplicate_barcode="No valid barcodes found (not current or previous year prefix)",
                        upload_date=datetime.now(),
                        created_by=user_instance
                    )
                    results.append({
                        'filename': file.name,
                        'barcodes_found': [],
                        'status': 'Failed (No valid barcodes found)'
                    })
                    continue

                is_duplicate = False
                for barcode_value in unique_found_barcodes:
                    if ScannedBarcode.objects.filter(barcode_value=barcode_value).exists():
                        DuplicateBarcodeException.objects.create(
                            file_name=file.name,
                            duplicate_barcode=barcode_value,
                            location_id =user_location_id,
                            upload_date=datetime.now(),
                            created_by=user_instance
                        )
                        is_duplicate = True
                        break 
                
                if is_duplicate:
                    results.append({
                        'filename': file.name,
                        'barcodes_found': list(unique_found_barcodes),
                        'status': 'Failed (Duplicate barcode)'
                    })
                    continue 

                # Use a transaction for data integrity
                with transaction.atomic():
                    shipping_label = ShippingLabelData(
                        path=file,
                        location_id =user_location_id,
                        user=user_instance,
                        upload_date=date_today,
                        created_by=user_instance
                    )
                    shipping_label.save()
                    
                    for barcode_value in unique_found_barcodes:
                        ScannedBarcode.objects.create(
                            shipping_label=shipping_label,
                            barcode_value=barcode_value,
                            created_by=user_instance
                        )
                    
                    # Update status after successful creation
                    shipping_label.status = 1
                    shipping_label.print_download_status = 0
                    shipping_label.save()

                results.append({
                    'filename': file.name,
                    'barcodes_found': list(unique_found_barcodes),
                    'status': 'Success'
                })

            except Exception as e:
                # Log any other exceptions
                DuplicateBarcodeException.objects.create(
                    file_name=file.name,
                    location_id =user_location_id,
                    upload_date=datetime.now(),
                    created_by_id=user_instance,
                    duplicate_barcode=f"Error processing file: {str(e)}"
                )
                results.append({
                    'filename': file.name,
                    'barcodes_found': [],
                    'status': f'Error: {str(e)}'
                })

        return JsonResponse({'total_files': len(uploaded_files), 'results': results})

    return render(request, 'upload.html')


def results_view(request):
    all_shipping_labels = ShippingLabelData.objects.all().order_by('-id')
    duplicate_exceptions = DuplicateBarcodeException.objects.all().order_by('-upload_date')
    
    return render(request, 'results.html', {
        'labels': all_shipping_labels,
        'exceptions': duplicate_exceptions
    })

def download_pdf(request):   
    user = request.user 
    user_permissions = get_user_permissions(user,'download')
    if user_permissions['can_view']:
        
            context = {               
                'permissions': user_permissions
            }
            return render(request, 'barcode_app/search.html', context)
    else:      
        return redirect('unautorized')

@csrf_exempt
def print_labels(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_ids = data.get('ids', [])
            
            if not selected_ids:
                return JsonResponse({'success': False, 'message': 'No files selected.'}, status=400)

            with transaction.atomic():
                selected_labels = ShippingLabelData.objects.filter(id__in=selected_ids)
                if not selected_labels.exists():
                    return JsonResponse({'success': False, 'message': 'Selected files not found.'}, status=404)
                
                ShippingLabelData.objects.filter(id__in=selected_ids).update(print_download_status=2)

                merged_pdf_buffer = BytesIO()
                merged_doc = fitz.open()

                for label in selected_labels:
                    try:
                        doc = fitz.open(label.path.path)
                        merged_doc.insert_pdf(doc)
                        doc.close()
                    except Exception:
                        continue 

                merged_doc.save(merged_pdf_buffer)
                merged_doc.close()
                merged_pdf_buffer.seek(0)
                
                response = FileResponse(merged_pdf_buffer, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="merged_barcodes.pdf"'
                return response

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def update_print_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            label_id = data.get('id')

            if not label_id:
                return JsonResponse({'success': False, 'message': 'No label ID provided.'}, status=400)

            updated_count = ShippingLabelData.objects.filter(id=label_id).update(print_download_status=1)
            
            if updated_count == 0:
                return JsonResponse({'success': False, 'message': 'Label not found or already updated.'}, status=404)

            return JsonResponse({'success': True, 'message': 'Status updated to Printed.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def update_selected_print_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_ids = data.get('ids', [])
            
            if not selected_ids:
                return JsonResponse({'success': False, 'message': 'No files selected.'}, status=400)

            updated_count = ShippingLabelData.objects.filter(id__in=selected_ids).update(print_download_status=1)

            if updated_count == 0:
                return JsonResponse({'success': False, 'message': 'Selected labels not found or already updated.'}, status=404)

            return JsonResponse({'success': True, 'message': f'Successfully updated {updated_count} labels to Printed status.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def search_barcode_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            barcode_values = data.get('barcodes')

            if not barcode_values or not isinstance(barcode_values, list):
                return JsonResponse({'success': False, 'message': 'Invalid or missing barcode values.'}, status=400)
            
            scanned_barcodes = ScannedBarcode.objects.filter(barcode_value__in=barcode_values)

            labels = ShippingLabelData.objects.filter(
                barcodes__in=scanned_barcodes
            ).distinct().select_related('user', 'location').prefetch_related(
                Prefetch('barcodes', queryset=ScannedBarcode.objects.filter(barcode_value__in=barcode_values))
            )
            
            labels_data = []
            for label in labels:
                labels_data.append({
                    'id': label.id,
                    'file_name': label.path.name,
                    'user': label.user.name if label.user else None,
                    'location_name': label.location.name if label.location else None,
                    'status': label.status,
                    'print_download_status': label.print_download_status,
                    'barcodes': [b.barcode_value for b in label.barcodes.all()]
                })

            if labels_data:
                return JsonResponse({'success': True, 'labels': labels_data})
            else:
                return JsonResponse({'success': False, 'message': 'No matching labels found.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

def search_exceptions(request):
    if request.method == 'POST':
        try:
            user_location_id = request.user.location_id
            
            # If the user has no location assigned, return an error
            if not user_location_id:
                return JsonResponse({'success': False, 'message': 'User has no location so kindly assign the location.'}, status=403)
            
            data = json.loads(request.body)
            from_date_str = data.get('from_date')
            to_date_str = data.get('to_date')

            if not from_date_str or not to_date_str:
                return JsonResponse({'success': False, 'message': 'Both from_date and to_date are required.'}, status=400)

            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            
            to_date_end = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            exceptions: QuerySet = DuplicateBarcodeException.objects.filter(
                upload_date__range=[from_date, to_date_end],
                location_id=user_location_id # Filter by the creator's location
            ).order_by('-upload_date')

            results = []
            for exc in exceptions:
                results.append({
                    'file_name': exc.file_name,
                    'duplicate_barcode': exc.duplicate_barcode,
                    'upload_date': exc.upload_date.strftime('%Y-%m-%d %H:%M:%S')
                })

            if results:
                return JsonResponse({'success': True, 'exceptions': results})
            else:
                return JsonResponse({'success': True, 'exceptions': [], 'message': 'No exceptions found for this date range.'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON in request body.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

def get_shipping_label(request, label_id):
    label = get_object_or_404(ShippingLabelData, pk=label_id)
    file_path = label.path.path
    
    if not file_path:
        raise Http404("File not found.")
        
    try:
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    except FileNotFoundError:
        raise Http404("File not found.")