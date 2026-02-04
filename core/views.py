from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Course


# Create your views here.
# def home(request):
#     return HttpResponse("Главная страница работает!")

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
    context = {
        'title': 'EduHub - Главная',
        'courses_count': Course.objects.count(),
    }
    return render(request, 'home.html', context)


def courses_list(request):
    courses = Course.objects.all()
    return render(request, 'core/courses.html', {'courses': courses})


def course_detail(request, course_slug):
    """
    Детальная страница курса по его слагу
    Доступны только опубликованные курсы (is_published=True)
    """
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    context = {
        'title': f'Курс: {course.title}',
        'course': course,
    }
    return render(request, 'core/course_detail.html', context)

def course_detail_by_slug(request, slug):
    course = get_object_or_404(Course, slug=slug)
    return render(request, 'core/course_detail.html', {'course': course})


def courses_list(request):
    search_query = request.GET.get('search', '')

    if search_query:
        courses = Course.objects.filter(title__icontains=search_query)
    else:
        courses = Course.objects.all()

    return render(request, 'core/courses.html', {
        'courses': courses,
        'search_query': search_query,
    })
# core/views.py - добавить временные views
def teachers(request):
    return render(request, 'core/teachers.html', {'title': 'Преподаватели'})

def schedule(request):
    return render(request, 'core/schedule.html', {'title': 'Расписание'})

def about(request):
    return render(request, 'core/about.html', {'title': 'О нас'})


# def schedule(request):
#     data = {
#         'title': 'Расписание занятий',
#         'courses': [
#             {
#                 'title': 'Математика',
#                 'teacher': 'Иванов И.И.',
#                 'is_active': True,
#                 'schedule': 'Пн, Ср 10:00-11:30'
#             },
#             {
#                 'title': 'Программирование',
#                 'teacher': 'Петрова А.С.',
#                 'is_active': True,
#                 'schedule': 'Вт, Чт 14:00-15:30'
#             },
#             {
#                 'title': 'Физика',
#                 'teacher': 'Сидоров В.П.',
#                 'is_active': False,  # неактивный курс
#                 'schedule': 'Пт 09:00-10:30'
#             }
#         ]
#     }
#     return render(request, 'schedule/index.html', data)
