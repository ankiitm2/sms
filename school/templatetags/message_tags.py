# school/templatetags/message_tags
from django import template

register = template.Library()

@register.filter
def unread_messages(user):
    return user.received_messages.filter(is_read=False).count()