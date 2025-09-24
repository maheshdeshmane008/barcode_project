import os
from PIL import Image
from pyzbar.pyzbar import decode

# Create a dummy image to test with
try:
    img = Image.new('RGB', (100, 100), color = 'red')

    # This decode call will trigger the library lookup
    print("Attempting to decode with pyzbar...")
    decode(img)
    print("Success! pyzbar can find and use the ZBar library.")

except Exception as e:
    print(f"An error occurred: {e}")
    print("pyzbar is likely installed, but it cannot find the ZBar C library.")
    print("Make sure 'libzbar-0.dll' is in a folder listed in your system's PATH.")