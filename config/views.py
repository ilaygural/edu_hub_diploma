# Функция для своего ответа на ошибку 404
from django.http import HttpResponseNotFound, HttpResponseServerError


def page_not_found(request, exception):
    return HttpResponseNotFound("""
        <h1>📚 Страница не найдена - Edu_Hub</h1>
        <p>Извините, запрашиваемая страница не существует.</p>
        <ul>
            <li><a href="/admin/">Войти в админку</a></li>
            <li><a href="/">На главную</a></li>
        </ul>
    """)

def server_error(request):
    return HttpResponseServerError("""
        <h1>⚠️ Ошибка сервера - Edu_Hub</h1>
        <p>Произошла внутренняя ошибка сервера.</p>
        <p>Мы уже работаем над исправлением!</p>
        <a href="/">Вернуться на главную</a>
    """)
