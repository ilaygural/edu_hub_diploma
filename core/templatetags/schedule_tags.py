# schedule/templatetags/schedule_tags.py
from django import template

register = template.Library()

@register.simple_tag
def is_weekend():
    from datetime import datetime
    if datetime.now().weekday() in [5, 6]:  # суббота, воскресенье
        return "Сегодня выходной! 🎉"
    else:
        return "Сегодня учебный день 📚"

# schedule/templatetags/schedule_tags.py
@register.inclusion_tag('schedule/parts/course_card.html')
def course_card(course):
    return {'course': course}