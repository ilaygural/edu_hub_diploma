from django.db import models
from django.urls import reverse


class PublishedManager(models.Manager):
    """Менеджер для получения только опубликованных курсов"""

    def get_queryset(self):
        return super().get_queryset().filter(is_published=Course.Status.PUBLISHED)


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название тега")
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL')

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('course_by_tag', kwargs={'tag_slug': self.slug})


class Course(models.Model):
    class Status(models.IntegerChoices):
        DRAFT = 0, 'Черновик'
        PUBLISHED = 1, 'Опубликовано'

    title = models.CharField(max_length=200, verbose_name='Название курса')
    description = models.TextField(blank=True, verbose_name='Описание')  # blank=True как в примере
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', default=0)
    slug = models.SlugField(max_length=200, unique=True, db_index=True, verbose_name='URL')
    code = models.CharField(max_length=20, unique=True, verbose_name="Код курса")
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    photo = models.ImageField(upload_to="photos/%Y/%m/%d/", default=None, blank=True, null=True, verbose_name="Фото")

    is_published = models.IntegerField(
        choices=Status.choices,
        default=Status.PUBLISHED,
        verbose_name='Статус')
    tags = models.ManyToManyField(
        Tag,
        related_name='courses',
        verbose_name='Теги'
    )
    objects = models.Manager()  # Менеджер по умолчанию
    published = PublishedManager()  # Наш кастомный менеджер

    teachers = models.ManyToManyField(
        'accounts.Teacher',
        related_name='courses',
        blank=True,
        verbose_name='Преподаватели'
    )

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


class CourseReview(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Курс"
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Имя'
    )
    email = models.EmailField(
        verbose_name="Email"
    )
    text = models.TextField(
        verbose_name='Отзыв'
    )
    rating = models.IntegerField(
        choices=[(i, f"{i} ★") for i in range(1, 6)],
        verbose_name='Оценка'
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Опубликован"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата"
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.course.title}'

class UploadFiles(models.Model):
    file = models.FileField(upload_to='uploads_model')
