menu = [
    {'title': '🏠 Главная', 'url_name': 'home'},
    {'title': '📚 Курсы', 'url_name': 'courses'},
    {'title': '👨‍🏫 Преподаватели', 'url_name': 'teachers'},
    {'title': '📅 Расписание', 'url_name': 'schedule'},
    {'title': 'ℹ️ О нас', 'url_name': 'about'},
    {'title': '🚀 KPI', 'url_name': 'kpi_dashboard'},
]
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
        context['cat_selected'] = None
        return context
