import uuid

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Value, BooleanField
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView, UpdateView, DeleteView

from accounts.models import Teacher
from .forms import CourseQuestionForm, ReviewForm, UploadFileForm
from .mixins import DataMixin
from .models import Course, Tag, UploadFiles


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


# def home(request):
#     """Главная страница"""
#     # count_courses = cache.get_or_set('courses_count', Course.objects.count, 60)
#     count_courses = Course.objects.count()
#     context = {
#         'title': 'EduHub - Главная',
#         'courses_count': count_courses,
#     }
#     return render(request, 'home.html', context)

class HomeView(DataMixin, TemplateView):
    template_name = 'home.html'
    title_page = 'Название страницы'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
    #     context['title'] = 'EduHub - Главная'
        context['courses_count'] = Course.objects.count()
    #     # main_menu приходит автоматически из контекстного процессора
        return context


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


class CourseListView(ListView):
    model = Course
    context_object_name = 'courses'
    allow_empty = False
    template_name = 'core/courses.html'
    paginate_by = 3

    def get_queryset(self):
        qs = Course.objects.all().prefetch_related('tags', 'teachers')
        search_query = self.request.GET.get('search', '')
        if search_query:
            qs = qs.filter(title__icontains=search_query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


def course_detail(request, course_slug):
    """
    Детальная страница курса по его слагу
    Доступны только опубликованные курсы (is_published=True)
    """
    course = get_object_or_404(
        Course.published.prefetch_related('tags', 'teachers'),
        slug=course_slug
    )
    context = {
        'title': f'Курс: {course.title}',
        'course': course,
    }
    return render(request, 'core/course_detail.html', context)

class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    slug_url_kwarg = 'course_slug'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Course.published.prefetch_related('tags', 'teachers'),
            slug=self.kwargs[self.slug_url_kwarg]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Курс: {self.object.title}"
        return context

def course_detail_by_slug(request, slug):
    course = get_object_or_404(
        Course.objects.prefetch_related('tags', 'teachers'),
        slug=slug
    )
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
    total = courses.count()
    context = {
        'title': f'Тег: {tag.name}',
        'tag': tag,
        'courses': courses,
        'total': total,
        'page_type': 'tag'  # Чтобы в шаблоне отличать от обычного списка
    }
    return render(request, 'core/courses_list.html', context)


# def ask_course_question(request, course_id):
#     course = get_object_or_404(Course, id=course_id)
#     if request.method == 'POST':
#         form = CourseQuestionForm(request.POST)
#         if form.is_valid():
#             # Данные из формы
#             name = form.cleaned_data['name']
#             email = form.cleaned_data['email']
#             question = form.cleaned_data['question']
#
#             # отправка письма (пока консоль)
#             subject = f"Вопрос по курсу: {course.title}"
#             message = f'От {name} ({email}\nВопрос: {question})'
#             send_mail(
#                 subject,
#                 message,
#                 email,  # от кого
#                 ['admin@edu-hub.ru'],  # кому (админ)
#                 fail_silently=False,
#             )
#             messages.success(request, 'Ваш вопрос отправлен. Мы ответим вам на email.')
#             # print(f"SLUG: '{course.slug}'")
#             return redirect('course_detail', course_slug=course.slug)
#     else:
#         form = CourseQuestionForm()
#     return render(request, 'core/ask_question.html', {
#         'form': form,
#         'course': course,
#         'title': f"Вопрос по курсе: {course.title}",
#     })


class AskQuestionView(FormView):
    template_name = 'core/ask_question.html'
    form_class = CourseQuestionForm

    def get_success_url(self):
        """Возвращаем URL курса после успешной отправки"""
        course = self.get_course()
        return reverse_lazy('course_detail', kwargs={'course_slug': course.slug})

    def get_course(self):
        """Вспомогательный метод для получения курса"""
        course_id = self.kwargs.get('course_id')
        return get_object_or_404(Course, id=course_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_course()
        context['course'] = course
        context['title'] = f"Вопрос по курсу: {course.title}"
        return context

    def form_valid(self, form):
        course = self.get_course()

        # Данные из формы
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        question = form.cleaned_data['question']

        # Отправка письма
        subject = f"Вопрос по курсу: {course.title}"
        message = f'От {name} ({email}\nВопрос: {question})'
        send_mail(
            subject,
            message,
            email,
            ['admin@edu-hub.ru'],
            fail_silently=False,
        )

        messages.success(self.request, 'Ваш вопрос отправлен. Мы ответим вам на email.')
        return super().form_valid(form)




# def add_review(request, course_id):
#     course = get_object_or_404(Course, id=course_id)
#     if request.method == 'POST':
#         form = ReviewForm(request.POST, user=request.user)
#         if form.is_valid():
#             review = form.save(commit=False)
#             review.course = course
#             if request.user.is_authenticated:
#                 review.user = request.user
#
#                 if not form.cleaned_data['name']:
#                     review.name = request.user.get_full_name() or request.user.username
#
#                 if not form.cleaned_data['email']:
#                     review.email = request.user
#             review.save()
#             messages.success(request, "Спасибо! Отзыв отправлен на модерацию")
#             return redirect('course_detail', course_slug=course.slug)
#     else:
#         form = ReviewForm(user=request.user)
#     return render(request, 'core/add_review.html', {
#         'form': form,
#         'course': course,
#         'title': f"Отзыв на курс: {course.title}",
#     })


class AddReviewView(FormView):
    template_name = 'core/add_review.html'
    form_class = ReviewForm

    def get_success_url(self):
        course = get_object_or_404(Course, id=self.kwargs['course_id'])
        return reverse_lazy('course_detail', kwargs={'course_slug': course.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, id=self.kwargs['course_id'])
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Если форма ожидает user
        if hasattr(self.form_class, 'user'):
            kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        review = form.save(commit=False)
        review.course_id = self.kwargs['course_id']
        review.save()
        messages.success(self.request, "Спасибо! Отзыв отправлен на модерацию")
        return super().form_valid(form)

# def teachers(request):
#     return render(request, 'core/teachers.html', {'title': 'Преподаватели'})


def schedule(request):
    return render(request, 'core/schedule.html', {'title': 'Расписание'})


# def handle_uploaded_file(f):
#     # print(f"СОХРАНЯЕМ ФАЙЛ: {f.name}")
#     name = f.name
#     ext = ""
#
#     if '.' in name:
#         ext = name[name.rindex('.'):]
#         name = name[:name.rindex('.')]
#     suffix = str(uuid.uuid4())
#     filename = f"uploads/{name}_{suffix}{ext}"
#     with open(filename, "wb+") as destination:
#         for chunk in f.chunks():
#             destination.write(chunk)
#     return filename


# def about(request):
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             saved_path = UploadFiles(file=form.cleaned_data['file'])
#             saved_path.save()
#             return render(request, 'core/about.html', {
#                 'form': form,
#                 'success': f'Файл сохранен: {saved_path}'
#             })
#     else:
#         form = UploadFileForm()
#     return render(request, 'core/about.html', {'form': form})

class AboutView(LoginRequiredMixin, View):
    def get(self, request):
        form = UploadFileForm()
        return render(request, 'core/about.html', {'form': form})

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            saved_path = UploadFiles(file=form.cleaned_data['file'])
            saved_path.save()
            return render(request, 'core/about.html', {
                'form': form,
                'success': f'Файл сохранен: {saved_path}'
            })
        return render(request, 'core/about.html', {'form': form})


class TeacherListView(ListView):
    model = Teacher
    template_name = 'core/teachers.html'
    context_object_name = 'teachers'


    def get_queryset(self):
        return Teacher.objects.all().prefetch_related('courses')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Наши преподаватели"
        return context

class CourseCreateView(CreateView):
    model = Course
    fields = ['title', 'description', 'price', 'code', 'photo', 'is_published', 'tags', 'teachers']
    template_name = 'core/course_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Добавление курса"
        return context

    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'course_slug': self.object.slug})


class CourseUpdateView(UpdateView):
    model = Course
    fields = ['title', 'description', 'price', 'code', 'photo', 'is_published', 'tags', 'teachers']
    template_name = 'core/course_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование: {self.object.title}'
        return context

    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'course_slug': self.object.slug})


class CourseDeleteView(DeleteView):
    model = Course
    template_name = 'core/course_confirm_delete.html'  # шаблон подтверждения
    success_url = reverse_lazy('courses')  # после удаления — на список

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Удаление курса: {self.object.title}'
        return context