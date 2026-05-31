from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

from .access import user_has_profile

menu = [
    {'title': '🏠 Главная', 'url_name': 'home'},
    {'title': '📚 Курсы', 'url_name': 'courses'},
    {'title': '👨‍🏫 Преподаватели', 'url_name': 'teachers'},
    {'title': '📅 Расписание', 'url_name': 'schedule'},
    {'title': 'ℹ️ О нас', 'url_name': 'about'},
]


class RoleRequiredMixin(LoginRequiredMixin):
    """Сначала вход, затем проверка профиля роли (manager / teacher / parent)."""

    required_profile = ''

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.required_profile and not user_has_profile(request.user, self.required_profile):
            messages.warning(
                request,
                'Кабинет этой роли для вашей учётной записи не назначен. Выберите другую роль.',
            )
            return redirect('users:role_select')
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class ManagerRequiredMixin(RoleRequiredMixin):
    required_profile = 'manager_profile'


class TeacherRequiredMixin(RoleRequiredMixin):
    required_profile = 'teacher_profile'


class ParentRequiredMixin(RoleRequiredMixin):
    required_profile = 'parent_profile'


class DataMixin:
    title_page = None
    extra_context = {}

    def __init__(self, **kwargs):
        if self.title_page:
            self.extra_context['title'] = self.title_page

        if 'menu' not in self.extra_context:
            self.extra_context['menu'] = menu

    def get_mixin_context(self, context, **kwargs):
        if self.title_page:
            context['title'] = self.title_page
        context['menu'] = menu
        return context
