# school/templatetags/timetable_tags
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)