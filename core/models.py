from django.db import models
from django.urls import reverse


class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название курса')
    description = models.TextField(blank=True, verbose_name='Описание')  # blank=True как в примере
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', default=0)
    slug = models.SlugField(max_length=200, unique=True, db_index=True, verbose_name='URL')
    code = models.CharField(max_length=20, unique=True, verbose_name="Код курса")
    # НОВЫЕ ПОЛЯ по аналогии с учебным проектом:
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'course_slug': self.slug})

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-time_create']  # новые курсы будут первыми
        indexes = [
            models.Index(fields=['-time_create']),  # Для быстрой сортировки
            models.Index(fields=['slug']),  # Для поиска по URL
        ]