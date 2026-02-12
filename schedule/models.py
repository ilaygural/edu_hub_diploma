from datetime import date, timedelta

from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from accounts.models import Pupil


# Create your models here.
class Group(models.Model):
    """
    Учебная группа
    """
    name = models.CharField(max_length=100, verbose_name="Название группы")
    description = models.TextField(blank=True, verbose_name="Описание группы")
    start_date = models.DateField(verbose_name="Дата создание")
    end_date = models.DateField(verbose_name="Дата окончания")

    class Status(models.IntegerChoices):
        ACTIVE = 1, 'Активна'
        COMPLETED = 2, 'Завершена'
        PLANNED = 3, 'Запланирована'

    status = models.IntegerField(
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус'
    )

    def __str__(self):
        return self.name

    def get_active_pupils(self):
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        return self.group_enrollments.filter(Q(date_to__isnull=True) | Q(date_to__gte=seven_days_ago)).values(
            'pupil')

    def has_active_pupils(self):
        return self.group_enrollments.filter(date_to__isnull=True).exists()

    def active_pupils_count(self):
        return self.group_enrollments.filter(date_to__isnull=True).count()

    class Meta:
        verbose_name = "Учебная группа"
        verbose_name_plural = "Учебные группы"
        ordering = ['-start_date']


class Enrollment(models.Model):
    """Зачисление ученика в группу"""
    pupil = models.ForeignKey(
        Pupil,
        on_delete=models.CASCADE,
        related_name='pupil_enrollments',
        verbose_name="Ученик"
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='group_enrollments',
        verbose_name="Группа"
    )

    date_from = models.DateField(verbose_name="Дата зачисления")
    date_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата отчисления"
    )

    def __str__(self):
        return f"{self.pupil} - {self.group}"

    @property
    def is_active(self):
        return self.date_to is None

    class Meta:
        verbose_name = "Зачисление"
        verbose_name_plural = "Зачисления"
        ordering = ['-date_from']


class Attendance(models.Model):
    """
    Посещаемость
    """
    pupil = models.ForeignKey(
        Pupil,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Ученик'
    )
    lesson_date = models.DateField(verbose_name='Дата занятий')

    class Status(models.IntegerChoices):
        PRESENT = 1, 'Присутствовал'
        ABSENT = 0, 'Отсутствовал'
        LATE = 2, 'Опоздал'

    status = models.IntegerField(
        choices=Status.choices,
        default=Status.PRESENT,
        verbose_name='Статус'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания'
    )

    def __str__(self):
        return f"{self.pupil} - {self.lesson_date}: {self.get_status_display()}"

    @property
    def is_present(self):
        return True if self.status == self.Status.PRESENT or self.status == self.Status.LATE else False

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемости"
        ordering = ['-lesson_date']


class Schedule(models.Model):
    """
    Конкретное занятие группы в определенное время
    """
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Группа'
    )

    lesson_date = models.DateField(verbose_name='Дата занятия')
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')

    topic = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Тема занятия'
    )

    teacher = models.ForeignKey(
        'accounts.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedule_lessons',
        verbose_name='Преподаватель'
    )

    def __str__(self):
        return f'{self.group} - {self.lesson_date}'

    @property
    def duration(self):
        # Преобразуем время в минуты от начала дня
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes  # Длительность в минутах

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'
        ordering = ['-lesson_date', 'start_time']  # новые курсы будут первыми
        indexes = [
            models.Index(fields=['-lesson_date']),  # Для быстрой сортировки
        ]


class Payment(models.Model):
    pupil = models.ForeignKey(
        Pupil,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name='Ученик'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма"
    )
    payment_date = models.DateField(
        verbose_name='Дата оплаты',
        default=date.today
    )

    class Purpose(models.IntegerChoices):
        TUITION = 0, "Обучение"
        MATERIAL = 1, "Материалы"
        OTHER = 2, "Прочее"

    purpose = models.IntegerField(
        choices=Purpose.choices,
        default=Purpose.TUITION,
        verbose_name='Назначение'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(
        blank=True,
        verbose_name='Примечания'
    )

    def __str__(self):
        return f'{self.pupil} - {self.amount} ₽ - {self.get_purpose_display()}'

    #  Метод Увеличение суммы платежа
    def increase_amount(self, value):
        self.amount = F('amount') + value
        self.save()
        self.refresh_from_db()

    @property
    def is_recent(self):
        return (timezone.now().date() - self.payment_date).days <= 30

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ['-payment_date']
