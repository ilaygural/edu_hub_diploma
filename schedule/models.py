from django.db import models

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
        return self.group_enrollments.filter(date_to__isnull=True).values('pupil')

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
