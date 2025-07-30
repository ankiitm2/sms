from .models import Notification

def create_notification(user, message):
    if user and user.is_authenticated:
        Notification.objects.create(user=user, message=message, notification_type='exam', title="Notification Title")