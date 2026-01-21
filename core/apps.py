from django.apps import AppConfig


class CoreConfig(AppConfig):  # ← ПЕРЕИМЕНОВАЛИ!
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'  # ← Важно!
    verbose_name = 'Основные модели'
