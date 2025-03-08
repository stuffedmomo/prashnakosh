"""
Context processors for the Prashnakosh application.
"""
from django.conf import settings

def google_analytics(request):
    """
    Add Google Analytics ID to the context if available.
    """
    return {
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', ''),
    }

def app_info(request):
    """
    Add application information to every context.
    """
    return {
        'APP_NAME': 'Prashnakosh',
        'APP_VERSION': '1.0.0',
        'SUPPORT_EMAIL': 'support@prashnakosh.in',
    } 