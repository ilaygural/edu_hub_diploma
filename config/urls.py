"""
URL configuration for edu_hub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the includes() function: from django.urls import includes, path
    2. Add a URL to urlpatterns:  path('blog/', includes('blog.urls'))
"""
from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from config import settings
from config.views import page_not_found, server_error
from core import views
from core.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    # path("", includes("schedule.urls")),
]  + debug_toolbar_urls()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = page_not_found  # добавление функции своего ответа
handler500 = server_error

#  Название панели администрирования
admin.site.site_header = "Панель администрирования"
admin.site.index_title = "Учебный Хаб"