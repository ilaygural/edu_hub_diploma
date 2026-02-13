from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.urls import reverse


class PupilManager(models.Manager):
    def active_or_enrolled_after(self, date):
        return self.filter(Q(status=Pupil.Status.ACTIVE)|Q(enrolled_date__gte=date))


# Create your models here.
class Pupil(models.Model):
    """
    Профиль ученика. Связан с User через OneToOne
    """
    # Основная связь с пользователями
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='pupil_profile',
        verbose_name='Пользователь'
    )

    # Личные данные (дополнительно к стандартным полям User)
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Адрес'
    )

    objects = PupilManager()

    # Статус ученика
    class Status(models.IntegerChoices):
        ACTIVE = 1, 'Активный'
        INACTIVE = 0, 'Неактивный'
        GRADUATED = 2, 'Выпускник'

    status = models.IntegerField(
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус'
    )

    # Даты
    enrolled_date = models.DateField(
        auto_now=True,
        verbose_name='Даты регистрации'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Последнее обновление'
    )

    class Meta:
        verbose_name = 'Ученик'
        verbose_name_plural = 'Ученики'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.user.username})'

    def get_absolute_url(self):
        return reverse('pupil_detail', kwargs={'pk': self.pk})

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email


    #  геттеры для отображения правильных имен в админке
    def get_full_name(self):
        return self.user.get_full_name()

    get_full_name.short_description = 'ФИО'

    def get_email(self):
        return self.user.email

    get_email.short_description = 'Email'

class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name="Пользователь"
    )
    qualification = models.CharField(max_length=200, blank=True, verbose_name="Квалификация")
    specialization = models.CharField(max_length=200, blank=True, verbose_name="Специализация")
    experience_years = models.IntegerField(default=0, verbose_name="Стаж(лет)")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    office = models.CharField(max_length=50, blank=True, verbose_name="Кабинет")
    is_active = models.BooleanField(default=True, verbose_name='Активный')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"
        ordering = ['user__last_name']

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.user.username})'

    @property
    def full_name(self):
        return self.user.get_full_name()

    def get_full_name(self):
        return self.user.get_full_name()

    get_full_name.short_description = 'ФИО'


class Parent(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        verbose_name='Пользователь'
    )

    children = models.ManyToManyField(
        Pupil,
        blank=True,
        verbose_name="Дети"
    )

    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    work_place = models.CharField(max_length=200, blank=True, verbose_name='Место работы')
    additional_contacts = models.TextField(blank=True, verbose_name="Дополнительные контакты")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Родитель'
        verbose_name_plural = 'Родители'
        ordering = ['user__last_name']

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.user.username})'

    @property
    def full_name(self):
        return self.user.get_full_name()

    def get_full_name(self):
        return self.user.get_full_name()

    get_full_name.short_description = 'ФИО'