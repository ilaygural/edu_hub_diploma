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
    patronymic = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отчество',
    )
    snils = models.CharField(
        max_length=14,
        blank=True,
        verbose_name='СНИЛС',
    )
    birth_certificate = models.TextField(
        blank=True,
        verbose_name='Свидетельство о рождении',
        help_text='Серия, номер, кем и когда выдано',
    )
    place_of_birth = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Место рождения',
    )
    pfdo_certificate_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Номер сертификата ПФДО',
        help_text='Если есть сертификат персонифицированного финансирования',
    )

    class IdentityDocument(models.IntegerChoices):
        BIRTH_CERTIFICATE = 1, 'Свидетельство о рождении'
        PASSPORT = 2, 'Паспорт'

    identity_document_type = models.IntegerField(
        choices=IdentityDocument.choices,
        default=IdentityDocument.BIRTH_CERTIFICATE,
        verbose_name='Документ ребёнка',
    )
    passport_series = models.CharField(max_length=10, blank=True, verbose_name='Серия паспорта')
    passport_number = models.CharField(max_length=10, blank=True, verbose_name='Номер паспорта')
    passport_issued_by = models.CharField(max_length=255, blank=True, verbose_name='Кем выдан')
    passport_issued_date = models.DateField(null=True, blank=True, verbose_name='Дата выдачи паспорта')

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
        auto_now_add=True,
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

    def contract_filled_fields(self) -> tuple[list[str], list[str]]:
        """(заполнено, не заполнено) — ключевые поля для договора."""
        user = self.user
        checks = {
            'Фамилия': bool(user.last_name.strip()),
            'Имя': bool(user.first_name.strip()),
            'Дата рождения': bool(self.birth_date),
        }
        if self.identity_document_type == self.IdentityDocument.BIRTH_CERTIFICATE:
            checks['Свидетельство о рождении'] = bool(self.birth_certificate.strip())
        else:
            checks['Паспорт ребёнка'] = bool(
                self.passport_series.strip() and self.passport_number.strip()
            )
        filled = [k for k, ok in checks.items() if ok]
        missing = [k for k, ok in checks.items() if not ok]
        return filled, missing

    @property
    def is_contract_data_complete(self) -> bool:
        _, missing = self.contract_filled_fields()
        return len(missing) == 0


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
        related_name='parents',
        verbose_name="Дети"
    )

    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    patronymic = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    work_place = models.CharField(max_length=200, blank=True, verbose_name='Место работы')
    additional_contacts = models.TextField(blank=True, verbose_name="Дополнительные контакты")
    class RepresentativeRelation(models.IntegerChoices):
        PARENT = 1, 'Родитель'
        LEGAL_GUARDIAN = 2, 'Законный представитель'

    representative_relation = models.IntegerField(
        choices=RepresentativeRelation.choices,
        default=RepresentativeRelation.PARENT,
        verbose_name='Статус',
        help_text='Как указано в договоре (родитель или законный представитель)',
    )
    address = models.CharField(max_length=255, blank=True, verbose_name='Домашний адрес')
    snils = models.CharField(max_length=14, blank=True, verbose_name='СНИЛС')
    passport_series = models.CharField(max_length=10, blank=True, verbose_name='Серия паспорта')
    passport_number = models.CharField(max_length=10, blank=True, verbose_name='Номер паспорта')
    passport_issued_by = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Кем выдан паспорт',
    )
    passport_issued_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата выдачи паспорта',
    )
    passport = models.TextField(
        blank=True,
        verbose_name='Прочие паспортные данные',
        help_text='Необязательно, если заполнены поля выше',
    )
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

    def contract_filled_fields(self) -> tuple[list[str], list[str]]:
        user = self.user
        checks = {
            'Фамилия': bool(user.last_name.strip()),
            'Имя': bool(user.first_name.strip()),
            'Телефон': bool(self.phone.strip()),
            'Домашний адрес': bool(self.address.strip()),
            'Отчество': bool(self.patronymic.strip()),
            'Серия и номер паспорта': bool(self.passport_series.strip() and self.passport_number.strip()),
            'Кем выдан паспорт': bool(self.passport_issued_by.strip()),
            'Дата выдачи паспорта': bool(self.passport_issued_date),
        }
        filled = [k for k, ok in checks.items() if ok]
        missing = [k for k, ok in checks.items() if not ok]
        return filled, missing

    @property
    def is_contract_data_complete(self) -> bool:
        _, missing = self.contract_filled_fields()
        return len(missing) == 0


class Manager(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='manager_profile',
        verbose_name='Пользователь'
    )
    department = models.CharField(max_length=100, blank=True, verbose_name='Отдел')
    position = models.CharField(max_length=100, blank=True, verbose_name='Должность')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Менеджер'
        verbose_name_plural = 'Менеджеры'

    def __str__(self):
        return f'{self.user.get_full_name()} (Менеджер)'