import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Using 2.0 Flash as requested
GEMINI_MODEL = "gemini-2.5-flash-lite" 
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

@csrf_exempt
def ocr_proxy(request):
    if request.method == 'GET':
        return JsonResponse({'message': 'OCR proxy endpoint is working', 'method': 'GET'})

    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        # Parse image from request (expects JSON body with {"base64_image": "data", "mime_type": "image/jpeg"})
        body = json.loads(request.body)
        base64_image = body.get('base64_image')
        mime_type = body.get('mime_type', 'image/jpeg')

        if not base64_image:
            return JsonResponse({'error': 'No base64_image data provided'}, status=400)

        # Prepare Gemini Payload
        payload = {
            "contents": [{
                "parts": [
                    {"text": "Extract these details from the Philippine driver's license: first_name, last_name, middle_name, license_number, home_address. Return ONLY a valid JSON object with these exact keys."},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_image
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        # Call Gemini API with key in headers
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }

        response = requests.post(GEMINI_ENDPOINT, json=payload, headers=headers, timeout=30)
        response_data = response.json()

        # Handle Errors from Gemini
        if response.status_code != 200:
            return JsonResponse({
                'error': 'Gemini API Error',
                'details': response_data
            }, status=response.status_code)

        # Extract and return the actual model response
        # For response_mime_type application/json, Gemini returns the JSON directly
        if 'candidates' in response_data and response_data['candidates']:
            extracted_data = response_data['candidates'][0]['content']['parts'][0]['text']
            # Try to parse as JSON
            try:
                parsed_data = json.loads(extracted_data)
                return JsonResponse(parsed_data)
            except json.JSONDecodeError:
                # If not valid JSON, return as text error
                return JsonResponse({'error': 'Invalid JSON response from Gemini', 'raw_response': extracted_data}, status=500)
        else:
            return JsonResponse({'error': 'No response from Gemini API'}, status=500)

    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'API request failed: {str(e)}'}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

def login_view(request):
    return render(request, "index.html")
