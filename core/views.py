from django.core.cache import cache
from django.db.models import Value, BooleanField
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Tag


# Create your views here.

def kpi_dashboard(request):
    """Представление для страницы с колючевыми показателями"""
    kpi_data = {
        'title': 'Ключевые показатели EduHub',
        'indicators': [
            {'name': 'Всего курсов', 'value': 12, 'change': '+2', 'icon': '📚'},
            {'name': 'Активных студентов', 'value': 143, 'change': '+5%', 'icon': '👨‍🎓'},
            {'name': 'Заполняемость групп', 'value': 87.5, 'change': '+2.3%', 'icon': '📊'},
            {'name': 'Средняя оценка', 'value': 4.7, 'change': '-0.1', 'icon': '⭐'},
        ],
        'updated': '29.01.2026 10:00',
    }
    return render(request, 'core/kpi_dashboard.html', context=kpi_data)


def home(request):
    """Главная страница"""
    count_courses = cache.get_or_set('courses_count', Course.objects.count, 60)
    context = {
        'title': 'EduHub - Главная',
        'courses_count': count_courses,
    }
    return render(request, 'home.html', context)


def courses_list(request):
    """Страница со списком всех курсов с поиском"""
    search_query = request.GET.get('search', '')

    qs = Course.objects.all().prefetch_related('tags', 'teachers')

    if search_query:
        qs = qs.filter(title__icontains=search_query)

    return render(request, 'core/courses.html', {
        'courses': qs,
        'search_query': search_query,
    })


def course_detail(request, course_slug):
    """
    Детальная страница курса по его слагу
    Доступны только опубликованные курсы (is_published=True)
    """
    course = get_object_or_404(Course.published, slug=course_slug)
    context = {
        'title': f'Курс: {course.title}',
        'course': course,
    }
    return render(request, 'core/course_detail.html', context)


def course_detail_by_slug(request, slug):
    course = get_object_or_404(Course, slug=slug)
    return render(request, 'core/course_detail.html', {'course': course})


def courses_by_tag(request, tag_slug):
    """
    Отображает все курсы с определенным тегом
    """
    tag = get_object_or_404(Tag, slug=tag_slug)
    courses = (
        Course.objects
        .filter(tags=tag)
        .prefetch_related('tags', 'teachers')
    )
    context = {
        'title': f'Тег: {tag.name}',
        'tag': tag,
        'courses': courses,
        'page_type': 'tag'  # Чтобы в шаблоне отличать от обычного списка
    }
    return render(request, 'core/courses_list.html', context)


def teachers(request):
    return render(request, 'core/teachers.html', {'title': 'Преподаватели'})


def schedule(request):
    return render(request, 'core/schedule.html', {'title': 'Расписание'})


def about(request):
    return render(request, 'core/about.html', {'title': 'О нас'})
