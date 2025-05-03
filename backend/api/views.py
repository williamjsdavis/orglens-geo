import os
import time # Optional: for slight delay if needed during testing
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseBadRequest
from rest_framework.decorators import api_view
from rest_framework.response import Response
from openai import OpenAI, APIError # Make sure to import OpenAI and potential errors
from django.conf import settings

# Initialize OpenAI client (using the key from settings)
try:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None # Set client to None if initialization fails


# --- Simple Test View ---
@api_view(['GET'])
def hello_world(request):
    """
    A simple endpoint to test if the backend is running and reachable.
    """
    return Response({"message": "Hello from Django!"})


# --- LLM Streaming View ---

def generate_openai_stream(prompt):
    """
    Generator function to stream responses from OpenAI API.
    Yields chunks of text content.
    """
    if not client:
        yield "Error: OpenAI client not initialized. Check API key."
        return
    if not prompt:
        yield "Error: No prompt provided."
        return

    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo", # Or your preferred model
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content
                # time.sleep(0.01) # Optional small delay for testing flow

    except APIError as e:
        print(f"OpenAI API Error: {e}")
        yield f"\n\nError communicating with OpenAI: {e.message}"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        yield f"\n\nAn unexpected error occurred: {str(e)}"


@api_view(['POST'])
def llm_stream_view(request):
    """
    Handles POST requests containing a 'prompt' and returns a StreamingHttpResponse
    with the OpenAI completion stream.
    """
    prompt = request.data.get('prompt')

    if not prompt:
        return HttpResponseBadRequest("Missing 'prompt' in request body.")

    if not client:
         return JsonResponse({"error": "OpenAI client not configured"}, status=503) # 503 Service Unavailable

    try:
        # Create the generator
        stream_generator = generate_openai_stream(prompt)

        # Return the streaming response
        # Use text/plain or text/event-stream depending on frontend handling
        # For the fetch API + manual decoding, text/plain is simple.
        response = StreamingHttpResponse(
            stream_generator,
            content_type='text/plain; charset=utf-8' # Simpler for basic fetch handling
            # content_type='text/event-stream' # Use this if using EventSource on frontend
        )
        # Optional: Add headers if needed for SSE (text/event-stream)
        # response['Cache-Control'] = 'no-cache'
        # response['X-Accel-Buffering'] = 'no' # Useful for Nginx buffering issues

        return response

    except Exception as e:
        # Catch potential errors during generator setup (though most are handled inside)
        print(f"Error setting up stream view: {e}")
        return JsonResponse({"error": f"Failed to start stream: {str(e)}"}, status=500)