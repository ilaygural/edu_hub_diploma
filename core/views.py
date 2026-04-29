from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from accounts.models import Teacher, Parent, Pupil
from schedule.models import Enrollment, Group
from .forms import CourseQuestionForm, ReviewForm, UploadFileForm
from .mixins import DataMixin
from .models import Course, Tag, UploadFiles
from django.views.generic.edit import CreateView
from .models import Application
from .forms import ApplicationForm


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


class ParentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/parent/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'parent_profile'):
            raise PermissionDenied  # или raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent = self.request.user.parent_profile  # связь OneToOne
        children = parent.children.all()  # все ученики этого родителя
        context['children'] = children
        context['title'] = 'Личный кабинет родителя'
        return context


class TeacherDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/teacher/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'teacher_profile'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile
        # Группы, которые ведёт педагог (предполагается, что в модели Schedule есть поле teacher)
        context['groups'] = teacher.schedule_lessons.all()  # или другая связь
        context['title'] = 'Личный кабинет педагога'
        return context


class ApplicationCreateView(CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'core/application_form.html'
    success_url = reverse_lazy('application_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Запись на курс'
        return context


class ManagerDashboardView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'core/manager/dashboard.html'
    context_object_name = 'applications'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'manager_profile'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        filter_by = self.request.GET.get('filter', 'new')
        if filter_by == 'approved':
            return Application.objects.filter(status='approved')
        elif filter_by == 'rejected':
            return Application.objects.filter(status='rejected')
        else:
            return Application.objects.filter(status='new')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['new_applications_count'] = Application.objects.filter(status='new').count()
        context['active_groups_count'] = Group.objects.filter(status=Group.Status.ACTIVE).count()
        context['pupils_count'] = Pupil.objects.count()
        context['recent_applications'] = Application.objects.order_by('-created_at')[:5]
        return context


User = get_user_model()


@login_required
def approve_application(request, pk):
    app = get_object_or_404(Application, pk=pk)
    password = get_random_string(8)
    # 1. Родитель
    parent_user, parent_created = User.objects.get_or_create(
        username=app.parent_email,
        defaults={
            'email': app.parent_email,
            'first_name': app.parent_name.split()[0] if app.parent_name else '',
            'last_name': app.parent_name.split()[-1] if len(app.parent_name.split()) > 1 else '',
        }
    )

    if parent_created:
        parent_user.set_password(password)
        parent_user.save()

    parent, _ = Parent.objects.get_or_create(
        user=parent_user,
        defaults={'phone': app.parent_phone}
    )

    # 2. Ученик
    pupil_username = app.child_name.replace(' ', '_').lower()
    pupil_user, pupil_created = User.objects.get_or_create(
        username=pupil_username,
        defaults={
            'first_name': app.child_name,
        }
    )

    if pupil_created:
        pupil_user.set_password(get_random_string(8))
        pupil_user.save()

    pupil, _ = Pupil.objects.get_or_create(
        user=pupil_user,
        defaults={'birth_date': None}
    )

    # 3. Связываем
    parent.children.add(pupil)

    # 4. Зачисление
    group = app.course.groups.first()
    if group:
        Enrollment.objects.get_or_create(
            pupil=pupil,
            group=group,
            defaults={'date_from': timezone.now().date()}
        )

    app.status = 'approved'
    app.save()
    send_mail(
        subject='Заявка одобрена',
        message=f'Ваша заявка на курс "{app.course.title}" одобрена.\n\n'
                f'Ваш логин: {app.parent_email}\n'
                f'Пароль: {password}\n\n'
                f'Войти в личный кабинет: http://127.0.0.1:8000/users/role-select/',

        from_email='admin@edu-hub.ru',
        recipient_list=[app.parent_email],
        fail_silently=True,
    )
    messages.success(request, f'Заявка на курс "{app.course.title}" одобрена.')
    return redirect('manager_dashboard')


@login_required
def reject_application(request, pk):
    app = get_object_or_404(Application, pk=pk)
    app.status = 'rejected'
    app.save()
    send_mail(
        subject='Заявка одобрена',
        message=f'Ваша заявка на курс "{app.course.title}" отклонена.',
        from_email='admin@edu-hub.ru',
        recipient_list=[app.parent_email],
        fail_silently=True,
    )
    messages.warning(request, f'Заявка на курс "{app.course.title}" отклонена.')
    return redirect('manager_dashboard')


def expel_pupil(request, pupil_id):
    pupil = get_object_or_404(Pupil, id=pupil_id)
    # Закрываем активное зачисление
    enrollment = Enrollment.objects.filter(pupil=pupil, date_to__isnull=True).first()
    if enrollment:
        enrollment.date_to = timezone.now().date()
        enrollment.save()
        messages.success(request, f'Ученик {pupil.user.get_full_name()} отчислен.')
    else:
        messages.error(request, 'Активное зачисление не найдено.')
    return redirect('manager_dashboard')


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


def manager_applications(request):
    filter_by = request.GET.get('filter', 'new')
    if filter_by == 'approved':
        applications = Application.objects.filter(status='approved')
    elif filter_by == 'rejected':
        applications = Application.objects.filter(status='rejected')
    else:
        applications = Application.objects.filter(status='new')
    return render(request, 'core/manager/applications.html', {'applications': applications})


def manager_pupils(request):
    pupils = Pupil.objects.all()
    return render(request, 'core/manager/pupils.html', {'pupils': pupils})


def manager_groups(request):
    return render(request, 'core/manager/groups.html')


def manager_schedule(request):
    return render(request, 'core/manager/schedule.html')


def manager_payments(request):
    return render(request, 'core/manager/payments.html')


def manager_reports(request):
    return render(request, 'core/manager/reports.html')
