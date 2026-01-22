from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Course

# Create your views here.

# core/views.py
# def home(request):
#     return HttpResponse("Главная страница работает!")
def home(request):
    """Главная страница"""
    context = {
        'title': 'EduHub - Главная',
        'courses_count': Course.objects.count(),
    }
    return render(request, 'home.html', context)

def schedule(request):
    data = {
        'title': 'Расписание занятий',
        'courses': [
            {
                'title': 'Математика',
                'teacher': 'Иванов И.И.',
                'is_active': True,
                'schedule': 'Пн, Ср 10:00-11:30'
            },
            {
                'title': 'Программирование',
                'teacher': 'Петрова А.С.',
                'is_active': True,
                'schedule': 'Вт, Чт 14:00-15:30'
            },
            {
                'title': 'Физика',
                'teacher': 'Сидоров В.П.',
                'is_active': False,  # неактивный курс
                'schedule': 'Пт 09:00-10:30'
            }
        ]
    }
    return render(request, 'schedule/index.html', data)


def courses_list(request):
    courses = Course.objects.all()
    return render(request, 'core/courses.html', {'courses': courses})


def course_details(request, course_id, pk):
    course = get_object_or_404(Course, id=pk)
    return render(request, 'core/course_detail.html', {'course': course})
