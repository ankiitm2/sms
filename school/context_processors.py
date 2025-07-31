# school/context_processors
from django.contrib.auth import get_user_model
from .models import Notification

def notifications(request):
    context = {}
    if request.user.is_authenticated:
        user = request.user
        context.update({
            'unread_notifications': user.notifications.filter(is_read=False).order_by('-created_at')[:5],
            'unread_notification_count': user.notifications.filter(is_read=False).count()
        })
    return context