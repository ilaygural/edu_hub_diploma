from django.http import HttpResponse
from django.shortcuts import render, redirect
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
    return HttpResponse("Список курсов")


def course_detail(request, course_id):
    if course_id > 100:  # несуществующий курс
        return redirect('home', permanent=False)
    return HttpResponse(f"Курс {course_id}")
