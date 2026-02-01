def site_menu(request):
    """Глобальное меню для всех шаблонов"""
    menu = [
        {'title': '🏠 Главная', 'url_name': 'home', 'active': False},
        {'title': '📚 Курсы', 'url_name': 'courses', 'active': False},
        {'title': '👨‍🏫 Преподаватели', 'url_name': 'teachers', 'active': False},
        {'title': '📅 Расписание', 'url_name': 'schedule', 'active': False},
        {'title': 'ℹ️ О нас', 'url_name': 'about', 'active': False},
        {'title': '🚀 KPI', 'url_name': 'kpi_dashboard', 'active': False},
    ]

    # Определяем активный пункт меню
    current_url = request.resolver_match.url_name if request.resolver_match else None
    for item in menu:
        if item['url_name'] == current_url:
            item['active'] = True

    return {'main_menu': menu}