"""
Utility functions for finance views
"""
import json
from django.http import HttpResponse


def add_htmx_trigger(response, event_name, data=None):
    """
    Add HX-Trigger header to response for HTMX events
    
    Args:
        response: HttpResponse object
        event_name: Name of the event to trigger
        data: Optional data to pass with the event
    
    Returns:
        HttpResponse with HX-Trigger header added
    """
    trigger_data = {event_name: data if data is not None else {}}
    
    # Check if HX-Trigger already exists
    existing_trigger = response.get('HX-Trigger', None)
    if existing_trigger:
        try:
            existing_data = json.loads(existing_trigger)
            existing_data.update(trigger_data)
            trigger_data = existing_data
        except (json.JSONDecodeError, TypeError):
            pass
    
    response['HX-Trigger'] = json.dumps(trigger_data)
    return response


def add_toast_trigger(response, message, toast_type='success'):
    """
    Add toast notification trigger to HTMX response
    
    Args:
        response: HttpResponse object
        message: Toast message text
        toast_type: Type of toast ('success', 'error', 'info')
    
    Returns:
        HttpResponse with toast trigger added
    """
    return add_htmx_trigger(response, 'show-toast', {
        'message': message,
        'type': toast_type
    })

