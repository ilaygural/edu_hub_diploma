from django import template
from django.core.cache import cache
from django.utils import timezone
from core.models import Course

register = template.Library()


# ==================== SIMPLE TAGS ====================

@register.simple_tag
def get_courses_count():
    """Возвращает общее количество курсов"""
    count = cache.get('courses_count')
    if count is None:
        count = cache.get_or_set('courses_count', Course.objects.count, 60)
        cache.set('courses_count', count, 60)  # кэш на 60 секунд
    return count


@register.simple_tag
def get_current_year():
    """Возвращает текущий год"""
    return timezone.now().year


@register.simple_tag
def format_price(amount):
    """Форматирует цену с разделителями тысяч"""
    if amount is None:
        return "0 ₽"
    return f"{amount:,} ₽".replace(",", " ")


# ==================== INCLUSION TAGS ====================

@register.inclusion_tag('core/includes/sidebar.html', takes_context=True)
def show_sidebar(context, current_page=None):
    # Пытаемся получить из кэша
    popular_courses = cache.get('popular_courses')
    if popular_courses is None:
        popular_courses = Course.objects.order_by('-time_create')[:3]
        cache.set('popular_courses', popular_courses, 300)  # 5 минут

    return {
        'popular_courses': popular_courses,
        'current_page': current_page,
        'user': context['request'].user,
    }


@register.inclusion_tag('core/includes/status_badge.html')
def show_status_badge():
    """Бейдж со статусом проекта"""
    return {
        'status': 'в разработке',
        'color': 'danger'  # danger, warning, success, info
    }