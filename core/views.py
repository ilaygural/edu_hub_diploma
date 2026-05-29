from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import FileResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from accounts.models import Teacher, Parent, Pupil
from schedule.models import Enrollment, Group, Schedule
from .forms import (
    CourseQuestionForm,
    ReviewForm,
    UploadFileForm,
    ParentProfileForm,
    PupilContractForm,
    KTPGenerationForm,
    KomplektovanieForm,
)
from .komplektovanie import build_komplektovanie_report, build_komplektovanie_xlsx
from .ktp import (
    build_ktp_xlsx,
    default_weekday_slot,
    split_lessons_for_template,
)
from .mixins import DataMixin
from .models import Course, Tag, UploadFiles
from django.views.generic.edit import CreateView
from .models import Application
from .forms import ApplicationForm
from schedule.models import Group, Schedule, Attendance
from accounts.models import Pupil


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
    fields = ['title', 'description', 'price', 'code', 'direction', 'photo', 'is_published', 'tags', 'teachers']
    template_name = 'core/course_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Добавление курса"
        return context

    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'course_slug': self.object.slug})


class CourseUpdateView(UpdateView):
    model = Course
    fields = ['title', 'description', 'price', 'code', 'direction', 'photo', 'is_published', 'tags', 'teachers']
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent = self.request.user.parent_profile
        children = parent.children.all()

        children_data = []
        for child in children:
            enrollments = child.pupil_enrollments.filter(date_to__isnull=True)
            for enrollment in enrollments:
                enrollment.schedule_list = Schedule.objects.filter(
                    group=enrollment.group,
                    status='approved'
                ).order_by('weekday', 'start_time')
            children_data.append({
                'child': child,
                'enrollments': enrollments
            })

        context['parent_profile'] = parent
        context['parent_contract_complete'] = parent.is_contract_data_complete
        context['children_contract_status'] = [
            {
                'child': child,
                'complete': child.is_contract_data_complete,
                'missing': child.contract_filled_fields()[1],
            }
            for child in children
        ]
        context['children_data'] = children_data
        return context


def _split_fio(full_name: str) -> tuple[str, str, str]:
    """Фамилия, имя, отчество из строки заявки."""
    parts = full_name.strip().split()
    if len(parts) >= 3:
        return parts[0], parts[1], ' '.join(parts[2:])
    if len(parts) == 2:
        return parts[0], parts[1], ''
    if len(parts) == 1:
        return '', parts[0], ''
    return '', '', ''


class ParentContractEditView(LoginRequiredMixin, View):
    """Данные родителя и детей для договора."""
    template_name = 'core/parent/profile_edit.html'
    success_url = reverse_lazy('parent_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'parent_profile'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _children(self):
        return self.request.user.parent_profile.children.select_related('user').order_by(
            'user__last_name', 'user__first_name',
        )

    def _enrollment_info(self, child):
        enrollment = (
            child.pupil_enrollments.filter(date_to__isnull=True)
            .select_related('group__course')
            .first()
        )
        if not enrollment or not enrollment.group.course_id:
            return None
        course = enrollment.group.course
        return {
            'course_title': course.title,
            'group_name': enrollment.group.name,
            'direction': course.direction_header or '—',
        }

    def _build_child_forms(self, data=None):
        forms_list = []
        for child in self._children():
            prefix = f'child_{child.pk}'
            if data is not None:
                form = PupilContractForm(data, instance=child, prefix=prefix)
            else:
                form = PupilContractForm(instance=child, prefix=prefix)
            forms_list.append({
                'child': child,
                'form': form,
                'enrollment': self._enrollment_info(child),
            })
        return forms_list

    def get(self, request):
        parent = request.user.parent_profile
        return render(request, self.template_name, {
            'parent_form': ParentProfileForm(instance=parent),
            'child_forms': self._build_child_forms(),
        })

    def post(self, request):
        parent = request.user.parent_profile
        parent_form = ParentProfileForm(request.POST, instance=parent)
        child_forms = self._build_child_forms(data=request.POST)
        all_valid = parent_form.is_valid() and all(item['form'].is_valid() for item in child_forms)

        if all_valid:
            parent_form.save()
            for item in child_forms:
                item['form'].save()
            messages.success(request, 'Данные для договора сохранены.')
            return redirect(self.success_url)

        messages.error(request, 'Проверьте форму: есть ошибки или незаполненные поля.')
        return render(request, self.template_name, {
            'parent_form': parent_form,
            'child_forms': child_forms,
        })


class TeacherDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/teacher/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        teacher = self.request.user.teacher_profile

        groups = Group.objects.filter(
            lessons__teacher=teacher
        ).distinct()
        lessons = (
            Schedule.objects.filter(teacher=teacher)
            .select_related('group__course')
            .order_by('lesson_date', 'start_time')[:15]
        )
        context['groups'] = groups
        context['upcoming_lessons'] = lessons
        return context


class TeacherGroupDetailView(DetailView):
    model = Group
    template_name = 'core/teacher/group_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        group = self.object

        context['pupils'] = group.group_enrollments.filter(
            date_to__isnull=True
        ).select_related('pupil')

        context['lessons'] = group.lessons.all().order_by('-lesson_date')

        return context


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Schedule
    template_name = "core/teacher/lesson_detail.html"
    context_object_name = "schedule"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        schedule = self.object  # ❗ ВАЖНО

        pupils = (
            schedule.group
            .group_enrollments
            .select_related('pupil__user')
        )

        context['pupils'] = pupils

        return context

    def post(self, request, *args, **kwargs):
        schedule = self.get_object()

        for key, value in request.POST.items():
            if key.startswith("status_"):
                pupil_id = key.split("_")[1]

                Attendance.objects.update_or_create(
                    schedule=schedule,
                    pupil_id=pupil_id,
                    defaults={"status": value}
                )

        return redirect(request.path)


class TeacherJournalView(LoginRequiredMixin, TemplateView):
    template_name = 'core/teacher/journal.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'teacher_profile'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _get_teacher_groups(self):
        teacher = self.request.user.teacher_profile
        return Group.objects.filter(teacher=teacher).select_related('course')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groups = self._get_teacher_groups()
        context['groups'] = groups
        group_id = self.request.GET.get('group')
        lesson_id = self.request.GET.get('lesson')
        selected_group = groups.filter(id=group_id).first() if group_id else None
        context['selected_group'] = selected_group
        if selected_group:
            lessons = selected_group.lessons.order_by('-lesson_date', 'start_time')
            context['lessons'] = lessons
            selected_lesson = lessons.filter(id=lesson_id).first() if lesson_id else None
            context['selected_lesson'] = selected_lesson
            if selected_lesson:
                enrollments = selected_group.group_enrollments.filter(
                    date_to__isnull=True
                ).select_related('pupil__user')
                attendance_qs = Attendance.objects.filter(schedule=selected_lesson)
                attendance_map = {a.pupil_id: a.status for a in attendance_qs}
                context['enrollments'] = enrollments
                context['attendance_map'] = attendance_map
        return context

    def post(self, request, *args, **kwargs):
        groups = self._get_teacher_groups()
        group_id = request.POST.get('group_id')
        lesson_id = request.POST.get('lesson_id')
        selected_group = groups.filter(id=group_id).first()
        if not selected_group:
            messages.error(request, 'Группа не найдена или недоступна.')
            return redirect('teacher_journal')
        lesson = get_object_or_404(Schedule, id=lesson_id, group=selected_group)
        enrollments = selected_group.group_enrollments.filter(date_to__isnull=True).select_related('pupil')
        valid_pupil_ids = {e.pupil_id for e in enrollments}
        for key, value in request.POST.items():
            if not key.startswith('status_'):
                continue
            pupil_id = int(key.split('_')[1])
            if pupil_id not in valid_pupil_ids:
                continue
            Attendance.objects.update_or_create(
                schedule=lesson,
                pupil_id=pupil_id,
                defaults={'status': int(value)}
            )
        messages.success(request, 'Посещаемость сохранена.')
        return redirect(f"{request.path}?group={group_id}&lesson={lesson_id}")


class TeacherKTPGenerateView(LoginRequiredMixin, FormView):
    """Генерация каркаса КТП (xlsx) по шаблону Excel."""

    form_class = KTPGenerationForm
    template_name = 'core/teacher/ktp_generate.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'teacher_profile'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user.teacher_profile
        return kwargs

    def form_valid(self, form):
        cleaned = form.cleaned_data
        half_year_choice = cleaned['half_year']
        skip_holidays = cleaned.get('skip_holidays', True)
        weekdays = cleaned['weekdays']

        period_configs: list[tuple[int, date, date]] = []
        if half_year_choice == 'both':
            period_configs = [
                (1, cleaned['date_from'], cleaned['date_to']),
                (2, cleaned['date_from_2'], cleaned['date_to_2']),
            ]
        else:
            period_configs = [
                (int(half_year_choice), cleaned['date_from'], cleaned['date_to']),
            ]

        periods: list[tuple[int, list[date], list[date]]] = []
        sorted_weekdays: list[str] = []

        for half_year, date_from, date_to in period_configs:
            try:
                left_dates, right_dates, sorted_weekdays = split_lessons_for_template(
                    date_from,
                    date_to,
                    weekdays,
                    skip_holidays=skip_holidays,
                )
            except ValueError as exc:
                form.add_error(None, str(exc))
                return self.form_invalid(form)

            lesson_count = len(left_dates) + len(right_dates)
            if lesson_count == 0:
                form.add_error(
                    None,
                    f'За период {half_year}-го полугодия не получено ни одной даты занятия.',
                )
                return self.form_invalid(form)
            periods.append((half_year, left_dates, right_dates))

        group = cleaned.get('group')
        group_name = str(group) if group else ''

        weekday_slot_1 = cleaned.get('weekday_slot_1') or default_weekday_slot(
            sorted_weekdays[0], default_time='10:30 - 12:00',
        )
        weekday_slot_2 = cleaned.get('weekday_slot_2') or default_weekday_slot(
            sorted_weekdays[1], default_time='10:00 - 11:30',
        )

        try:
            buffer = build_ktp_xlsx(
                periods,
                group_name=group_name,
                weekday_slot_1=weekday_slot_1,
                weekday_slot_2=weekday_slot_2,
            )
        except (FileNotFoundError, ValueError) as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)

        if half_year_choice == 'both':
            filename = (
                f"ktp_both_{cleaned['date_from']}_{cleaned['date_to']}_"
                f"{cleaned['date_from_2']}_{cleaned['date_to_2']}.xlsx"
            )
        else:
            filename = f"ktp_{half_year_choice}half_{cleaned['date_from']}_{cleaned['date_to']}.xlsx"
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )


class TeacherLessonView(DetailView):
    model = Schedule
    template_name = 'core/teacher/lesson_detail.html'
    context_object_name = 'schedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        schedule = self.object

        pupils = schedule.group.group_enrollments.select_related('pupil__user')

        context['pupils'] = pupils
        return context


@login_required
def save_attendance(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        if not group_id:
            return redirect('teacher_dashboard')

        for key, status_str in request.POST.items():
            if key.startswith('attendance_'):
                parts = key.split('_')
                if len(parts) != 3:
                    continue
                pupil_id = parts[1]
                lesson_date = parts[2]

                # Преобразуем строку статуса в число
                if status_str == 'present':
                    status = 1
                elif status_str == 'absent':
                    status = 0
                elif status_str == 'late':
                    status = 2
                else:
                    continue

                Attendance.objects.update_or_create(
                    pupil_id=pupil_id,
                    lesson_date=lesson_date,
                    defaults={'status': status}
                )
        return redirect(f'{request.path}?group={group_id}')
    return redirect('teacher_dashboard')


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
        context['recent_applications'] = Application.objects.filter(status='new').order_by('-created_at')[:5]
        return context


User = get_user_model()


@login_required
def approve_application(request, pk):
    app = get_object_or_404(Application, pk=pk)
    password = get_random_string(8)
    # 1. Родитель
    parent_last, parent_first, parent_patronymic = _split_fio(app.parent_name)
    parent_user, parent_created = User.objects.get_or_create(
        username=app.parent_email,
        defaults={
            'email': app.parent_email,
            'first_name': parent_first,
            'last_name': parent_last,
        },
    )

    if parent_created:
        parent_user.set_password(password)
        parent_user.save()

    parent, _ = Parent.objects.get_or_create(
        user=parent_user,
        defaults={'phone': app.parent_phone},
    )
    if app.parent_phone and not parent.phone:
        parent.phone = app.parent_phone
    if parent_patronymic and not parent.patronymic:
        parent.patronymic = parent_patronymic
    if parent_last and not parent_user.last_name:
        parent_user.last_name = parent_last
    if parent_first and not parent_user.first_name:
        parent_user.first_name = parent_first
    parent.save()
    parent_user.save()

    # 2. Ученик
    child_last, child_first, child_patronymic = _split_fio(app.child_name)
    pupil_username = app.child_name.replace(' ', '_').lower()[:150]
    pupil_user, pupil_created = User.objects.get_or_create(
        username=pupil_username,
        defaults={
            'first_name': child_first or app.child_name,
            'last_name': child_last,
        },
    )

    if pupil_created:
        pupil_user.set_password(get_random_string(8))
        pupil_user.save()

    pupil, _ = Pupil.objects.get_or_create(
        user=pupil_user,
        defaults={'birth_date': None},
    )
    if child_patronymic and not pupil.patronymic:
        pupil.patronymic = child_patronymic
    if child_last and not pupil_user.last_name:
        pupil_user.last_name = child_last
    if child_first and not pupil_user.first_name:
        pupil_user.first_name = child_first
    pupil.save()
    pupil_user.save()

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


def _require_manager(request):
    if not hasattr(request.user, 'manager_profile'):
        raise PermissionDenied


def manager_applications(request):
    _require_manager(request)
    filter_by = request.GET.get('filter', 'new')
    if filter_by == 'approved':
        applications = Application.objects.filter(status='approved')
    elif filter_by == 'rejected':
        applications = Application.objects.filter(status='rejected')
    else:
        applications = Application.objects.filter(status='new')
    return render(request, 'core/manager/applications.html', {'applications': applications})


def manager_pupils(request):
    _require_manager(request)
    pupils = (
        Pupil.objects
        .select_related('user')
        .prefetch_related(
            'pupil_enrollments__group__course',
            'parents__user',
        )
        .order_by('user__last_name', 'user__first_name')
    )
    return render(request, 'core/manager/pupils.html', {'pupils': pupils})


@login_required
def manager_pupil_contract(request, pupil_id):
    _require_manager(request)
    pupil = get_object_or_404(
        Pupil.objects.select_related('user').prefetch_related('parents__user'),
        pk=pupil_id,
    )
    parents = list(pupil.parents.all())
    enrollments = (
        pupil.pupil_enrollments.filter(date_to__isnull=True)
        .select_related('group__course')
        .order_by('-date_from')
    )
    return render(request, 'core/manager/pupil_contract.html', {
        'pupil': pupil,
        'parents': parents,
        'enrollments': enrollments,
        'pupil_missing': pupil.contract_filled_fields()[1],
        'parents_status': [
            {
                'parent': parent,
                'missing': parent.contract_filled_fields()[1],
                'complete': parent.is_contract_data_complete,
            }
            for parent in parents
        ],
    })


def manager_groups(request):
    return render(request, 'core/manager/groups.html')


def manager_schedule(request):
    group_id = request.GET.get('group')
    schedules = (
        Schedule.objects
        .select_related('group__course', 'teacher__user')
        .order_by('-lesson_date', 'start_time')
    )
    if group_id:
        schedules = schedules.filter(group_id=group_id)
    groups = Group.objects.select_related('course').order_by('course__title', 'name')
    return render(request, 'core/manager/schedule.html', {
        'schedules': schedules,
        'groups': groups,
        'selected_group_id': str(group_id) if group_id else '',
    })


def manager_payments(request):
    return render(request, 'core/manager/payments.html')


def manager_reports(request):
    _require_manager(request)

    komplektovanie_form = KomplektovanieForm(
        request.POST if request.method == 'POST' else None,
        initial={'report_date': timezone.localdate()},
    )
    komplektovanie_preview = None
    komplektovanie_warnings = []

    if request.method == 'POST' and komplektovanie_form.is_valid():
        report_date = komplektovanie_form.cleaned_data['report_date']
        if 'download_komplektovanie' in request.POST:
            try:
                buffer = build_komplektovanie_xlsx(report_date)
            except (FileNotFoundError, ValueError) as exc:
                messages.error(request, str(exc))
            else:
                filename = f'komplektovanie_{report_date:%Y-%m-%d}.xlsx'
                return FileResponse(
                    buffer,
                    as_attachment=True,
                    filename=filename,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
        elif 'preview_komplektovanie' in request.POST:
            report = build_komplektovanie_report(report_date)
            komplektovanie_preview = report.directions
            komplektovanie_warnings = report.warnings

    new_count = Application.objects.filter(status='new').count()
    approved_count = Application.objects.filter(status='approved').count()
    rejected_count = Application.objects.filter(status='rejected').count()
    active_groups_count = Group.objects.filter(status=Group.Status.ACTIVE).count()

    recent_applications = (
        Application.objects
        .select_related('course')
        .order_by('-created_at')[:10]
    )

    groups_stats = (
        Group.objects
        .select_related('course', 'teacher__user')
        .order_by('course__title', 'name')[:15]
    )

    return render(request, 'core/manager/reports.html', {
        'new_count': new_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'active_groups_count': active_groups_count,
        'recent_applications': recent_applications,
        'groups_stats': groups_stats,
        'komplektovanie_form': komplektovanie_form,
        'komplektovanie_preview': komplektovanie_preview,
        'komplektovanie_warnings': komplektovanie_warnings,
    })
