from django.db import models


class Course(models.Model):
    """Учебный курс/предмет"""
    title = models.CharField(max_length=200, verbose_name="Название курса")
    code = models.CharField(max_length=20, unique=True, verbose_name="Код курса")
    description = models.TextField(blank=True, verbose_name="Описание")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")

    def __str__(self):
        return f"{self.code} - {self.title}"

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"