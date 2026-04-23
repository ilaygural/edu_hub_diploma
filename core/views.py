from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from accounts.models import Teacher
from .forms import CourseQuestionForm, ReviewForm, UploadFileForm
from .mixins import DataMixin
from .models import Course, Tag, UploadFiles


class HomeView(DataMixin, TemplateView):
    template_name = 'home.html'
    title_page = 'Название страницы'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses_count'] = Course.objects.count()
        return context


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


class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Course.published.prefetch_related('tags', 'teachers'),
            slug=self.kwargs[self.slug_url_kwarg]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Курс: {self.object.title}"
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
    template_name = 'core/course_confirm_delete.html'
    success_url = reverse_lazy('courses')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Удаление курса: {self.object.title}'
        return context


class AskQuestionView(FormView):
    template_name = 'core/ask_question.html'
    form_class = CourseQuestionForm

    def get_success_url(self):
        course = self.get_course()
        return reverse_lazy('course_detail', kwargs={'course_slug': course.slug})

    def get_course(self):
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

        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        question = form.cleaned_data['question']

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


class AddReviewView(FormView):
    template_name = 'core/add_review.html'
    form_class = ReviewForm

    def get_success_url(self):
        course = get_object_or_404(Course, id=self.kwargs['course_id'])
        return reverse_lazy('course_detail', kwargs={'slug': course.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, id=self.kwargs['course_id'])
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.form_class, 'user'):
            kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        review = form.save(commit=False)
        review.course = get_object_or_404(Course, id=self.kwargs['course_id'])
        review.save()
        messages.success(self.request, "Спасибо! Отзыв отправлен на модерацию")
        return super().form_valid(form)


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


# Заглушки пока нужны надо понять связи и удалить
def schedule(request):
    return render(request, 'core/schedule.html', {'title': 'Расписание'})


def courses_by_tag(request, tag_slug):
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
        'page_type': 'tag'
    }
    return render(request, 'core/courses_list.html', context)

from django.views.generic.edit import CreateView
from .models import Application
from .forms import ApplicationForm

class ApplicationCreateView(CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'core/application_form.html'
    success_url = reverse_lazy('application_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Запись на курс'
        return context