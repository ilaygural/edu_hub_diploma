# config/urls.py
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Пока убираем остальные маршруты - добавим позже
]

