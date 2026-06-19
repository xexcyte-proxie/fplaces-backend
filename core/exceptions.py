from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework that unifies all error responses.
    Format: {"status": "error", "message": "User-friendly message", "details": {...}}
    """
    # Call REST framework's default exception handler first to get standard response
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'status': 'error',
            'message': 'An error occurred while processing your request.',
            'details': response.data
        }
        
        # Add user-friendly messages based on HTTP status codes
        if response.status_code == 401:
            custom_response_data['message'] = "Authentication credentials were not provided or are invalid. Please log in again."
        elif response.status_code == 403:
            custom_response_data['message'] = "You do not have the required permissions to perform this action."
        elif response.status_code == 404:
            custom_response_data['message'] = "The requested resource could not be found."
        elif response.status_code == 400:
            custom_response_data['message'] = "There was a problem with the data submitted. Please check the details and try again."
        elif response.status_code >= 500:
            custom_response_data['message'] = "A server error occurred. Our team has been notified."
            
        response.data = custom_response_data
    else:
        # If response is None, it means it's an unhandled server exception (500)
        logger.error(f"Unhandled API Exception: {exc}", exc_info=True)
        
        # Return a managed, user-friendly JSON response instead of allowing Django
        # to return an HTML 500 error page or a backend stack trace.
        custom_response_data = {
            'status': 'error',
            'message': 'An unexpected server error occurred. Our team has been notified.',
            'details': None
        }
        response = Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
