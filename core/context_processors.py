def site_menu(request):
    """Глобальное меню для всех шаблонов"""
    menu = [
        {'title': '🏠 Главная', 'url_name': 'home', 'active': False},
        {'title': '📚 Курсы', 'url_name': 'courses', 'active': False},
        {'title': '👨‍🏫 Преподаватели', 'url_name': 'teachers', 'active': False},
        {'title': '📅 Расписание', 'url_name': 'schedule', 'active': False},
        {'title': 'ℹ️ О нас', 'url_name': 'about', 'active': False},
        # {'title': '🚀 KPI', 'url_name': 'kpi_dashboard', 'active': False},
    ]

    # Определяем активный пункт меню
    current_url = request.resolver_match.url_name if request.resolver_match else None
    for item in menu:
        if item['url_name'] == current_url:
            item['active'] = True

    return {'main_menu': menu}


def messaging_unread(request):
    if not request.user.is_authenticated:
        return {}
    if hasattr(request.user, 'parent_profile'):
        from core.messaging import unread_count_for_parent

        return {
            'unread_messages_count': unread_count_for_parent(request.user.parent_profile),
        }
    if hasattr(request.user, 'teacher_profile'):
        from core.messaging import unread_count_for_teacher

        return {
            'unread_messages_count': unread_count_for_teacher(request.user.teacher_profile),
        }
    return {}