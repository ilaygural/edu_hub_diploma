from django import template
from django.utils import timezone
from core.models import Course

register = template.Library()


# ==================== SIMPLE TAGS ====================

@register.simple_tag
def get_courses_count():
    """Возвращает общее количество курсов"""
    return Course.objects.count()


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


@register.simple_tag
def get_project_status():
    """Статус проекта для отображения в шапке/футере"""
    return {
        'text': 'в разработке',
        'color': '#e74c3c',
        'icon': '🚧'
    }


# ==================== INCLUSION TAGS ====================

@register.inclusion_tag('core/includes/sidebar.html')
def show_sidebar(current_page='home'):
    """Сайдбар с популярными курсами"""
    return {
        'popular_courses': Course.objects.all()[:3],
        'current_page': current_page,
    }


@register.inclusion_tag('core/includes/status_badge.html')
def show_status_badge():
    """Бейдж со статусом проекта"""
    return {
        'status': 'в разработке',
        'color': 'danger'  # danger, warning, success, info
    }


# ==================== FILTERS (дополнительно) ====================

@register.filter
def shorten(text, length=50):
    """Сокращает текст до указанной длины"""
    if len(text) <= length:
        return text
    return text[:length] + "..."