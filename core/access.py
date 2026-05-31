"""Проверки доступа: гость → логин, чужая роль → выбор роли с сообщением."""
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect

from accounts.models import Manager, Parent, Teacher

PROFILE_MODELS = {
    'parent_profile': Parent,
    'teacher_profile': Teacher,
    'manager_profile': Manager,
}


def user_has_profile(user, profile_attr: str) -> bool:
    model = PROFILE_MODELS.get(profile_attr)
    if model is None:
        return False
    return model.objects.filter(user_id=user.pk).exists()


def require_role(request, profile_attr: str):
    """
    None — доступ разрешён;
    HttpResponse — редирект (на логин или на выбор роли).
    """
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not user_has_profile(request.user, profile_attr):
        messages.warning(
            request,
            'Кабинет этой роли для вашей учётной записи не назначен. Выберите другую роль.',
        )
        return redirect('users:role_select')
    return None


def require_manager(request):
    return require_role(request, 'manager_profile')


def require_teacher(request):
    return require_role(request, 'teacher_profile')


def require_parent(request):
    return require_role(request, 'parent_profile')
