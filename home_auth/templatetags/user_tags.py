# home_auth/templatetags/user_tags
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def user_avatar(user, size='normal'):
    if user.profile_picture and hasattr(user.profile_picture, 'url'):
        return user.profile_picture.url
    
    # Return different defaults based on size
    if size == 'small':
        return settings.STATIC_URL + 'img/profiles/avatar-02.jpg'
    return settings.STATIC_URL + 'img/profiles/avatar-01.jpg'