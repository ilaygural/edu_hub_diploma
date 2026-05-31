"""
Демо-данные для ВКР: курсы, группы, родители, дети, переписка.

Запуск:
    python manage.py seed_demo
    python manage.py seed_demo --password demo1234
    python manage.py seed_demo --clear   # удалить только demo_* пользователей и связанное
"""
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Manager, Parent, Pupil, Teacher
from core.messaging import get_or_create_thread, post_message
from core.models import Course
from schedule.models import Enrollment, Group, Schedule

User = get_user_model()
DEMO_PREFIX = 'demo_'


class Command(BaseCommand):
    help = 'Заполняет БД небольшим набором демо-данных для защиты ВКР'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default='demo1234',
            help='Пароль для всех demo-пользователей (по умолчанию demo1234)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить ранее созданные сущности с логином demo_*',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        if options['clear']:
            self._clear_demo()
            self.stdout.write(self.style.WARNING('Демо-данные demo_* удалены.'))

        today = timezone.localdate()
        year_start = date(today.year, 9, 1)
        if today.month < 9:
            year_start = date(today.year - 1, 9, 1)
        year_end = date(year_start.year + 1, 5, 31)

        manager_user = self._user(
            f'{DEMO_PREFIX}manager',
            password,
            first_name='Анна',
            last_name='Менеджерова',
            email='demo.manager@edu-hub.local',
        )
        Manager.objects.get_or_create(user=manager_user, defaults={'department': 'Приёмная'})

        t1 = self._teacher(
            password,
            username=f'{DEMO_PREFIX}teacher_ivanov',
            last_name='Иванов',
            first_name='Иван',
            patronymic='Иванович',
            email='ivanov@edu-hub.local',
        )
        t2 = self._teacher(
            password,
            username=f'{DEMO_PREFIX}teacher_petrova',
            last_name='Петрова',
            first_name='Мария',
            patronymic='Сергеевна',
            email='petrova@edu-hub.local',
        )

        courses = [
            self._course(
                'Вокруг света',
                'KURS-EST-01',
                Course.Direction.NATURAL_SCIENCE,
                [t1],
            ),
            self._course(
                'Робототехника',
                'KURS-TECH-01',
                Course.Direction.TECHNICAL,
                [t2],
            ),
            self._course(
                'Театральная студия',
                'KURS-ART-01',
                Course.Direction.ARTISTIC,
                [t1],
            ),
            self._course(
                'Шахматный клуб',
                'KURS-SOC-01',
                Course.Direction.SOCIAL_HUMANITIES,
                [t2],
            ),
        ]

        g1 = self._group(courses[0], 'Группа 1', t1, year_start, year_end)
        g2 = self._group(courses[1], 'Группа 1', t2, year_start, year_end)
        g3 = self._group(courses[2], 'Группа 1', t1, year_start, year_end)

        parent1 = self._parent(
            password,
            username=f'{DEMO_PREFIX}parent_smirnov',
            last_name='Смирнов',
            first_name='Алексей',
            patronymic='Петрович',
            email='smirnov@edu-hub.local',
            phone='+7 (913) 111-22-33',
            address='г. Томск, ул. Ленина, 46, кв. 12',
        )
        parent2 = self._parent(
            password,
            username=f'{DEMO_PREFIX}parent_kuznetsova',
            last_name='Кузнецова',
            first_name='Елена',
            patronymic='Андреевна',
            email='kuznetsova@edu-hub.local',
            phone='+7 (913) 444-55-66',
            address='г. Томск, ул. Елизаровых, 70А, кв. 5',
        )

        # Возраста на дату среза: ~8, ~11, ~14 лет
        pupil1 = self._pupil(
            password,
            username=f'{DEMO_PREFIX}pupil_artem',
            last_name='Смирнов',
            first_name='Артём',
            patronymic='Алексеевич',
            birth_date=date(today.year - 8, 3, 15),
            address='г. Томск, ул. Ленина, 46, кв. 12',
        )
        pupil2 = self._pupil(
            password,
            username=f'{DEMO_PREFIX}pupil_sofia',
            last_name='Кузнецова',
            first_name='София',
            patronymic='Еленовна',
            birth_date=date(today.year - 11, 7, 2),
            address='г. Томск, ул. Елизаровых, 70А, кв. 5',
        )
        pupil3 = self._pupil(
            password,
            username=f'{DEMO_PREFIX}pupil_maksim',
            last_name='Кузнецова',
            first_name='Максим',
            patronymic='Еленович',
            birth_date=date(today.year - 14, 1, 20),
            address='г. Томск, ул. Елизаровых, 70А, кв. 5',
        )

        parent1.children.add(pupil1)
        parent2.children.add(pupil2, pupil3)

        self._enroll(pupil1, g1, year_start)
        self._enroll(pupil1, g3, year_start)  # два кружка — для проверки кружковцев
        self._enroll(pupil2, g2, year_start)
        self._enroll(pupil3, g2, year_start)

        self._schedule(g1, t1, today, 'monday', time(10, 30), time(12, 0))
        self._schedule(g1, t1, today, 'thursday', time(10, 0), time(11, 30))
        self._schedule(g2, t2, today, 'tuesday', time(14, 0), time(15, 30))

        thread = get_or_create_thread(pupil1, parent1, t1)
        if not thread.messages.exists():
            post_message(
                thread,
                parent1.user,
                'Здравствуйте! Подскажите, пожалуйста, расписание занятий на следующую неделю.',
            )
            post_message(
                thread,
                t1.user,
                'Добрый день! Занятия по понедельникам и четвергам, 10:30–12:00. Кабинет уточним в журнале.',
            )

        self.stdout.write(self.style.SUCCESS('Демо-данные созданы (логины с префиксом demo_).'))
        self.stdout.write('')
        self.stdout.write('Пароль для всех demo-аккаунтов: %s' % password)
        self.stdout.write('Менеджер:     %s' % manager_user.username)
        self.stdout.write('Педагог 1:    %s' % t1.user.username)
        self.stdout.write('Педагог 2:    %s' % t2.user.username)
        self.stdout.write('Родитель 1:   %s' % parent1.user.username)
        self.stdout.write('Родитель 2:   %s' % parent2.user.username)
        self.stdout.write('Ученики:      %s, %s, %s' % (
            pupil1.user.username, pupil2.user.username, pupil3.user.username,
        ))
        self.stdout.write('')
        self.stdout.write('Вход: /users/login/ -> /users/role-select/')

    def _clear_demo(self):
        demo_users = User.objects.filter(username__startswith=DEMO_PREFIX)
        # CASCADE удалит профили, сообщения и т.д.
        Course.objects.filter(code__startswith='KURS-').delete()
        demo_users.delete()

    def _user(self, username, password, first_name, last_name, email):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            },
        )
        if created:
            user.set_password(password)
            user.save()
        return user

    def _teacher(self, password, username, last_name, first_name, patronymic, email):
        user = self._user(username, password, first_name, last_name, email)
        teacher, _ = Teacher.objects.get_or_create(
            user=user,
            defaults={'patronymic': patronymic, 'phone': '+7 (3822) 00-00-01'},
        )
        if not teacher.patronymic:
            teacher.patronymic = patronymic
            teacher.save(update_fields=['patronymic'])
        return teacher

    def _parent(self, password, username, last_name, first_name, patronymic, email, phone, address):
        user = self._user(username, password, first_name, last_name, email)
        parent, _ = Parent.objects.get_or_create(
            user=user,
            defaults={
                'patronymic': patronymic,
                'phone': phone,
                'address': address,
                'passport_series': '6915',
                'passport_number': '123456',
                'passport_issued_by': 'УФМС России по Томской области',
                'passport_issued_date': date(2015, 6, 1),
                'representative_relation': Parent.RepresentativeRelation.PARENT,
            },
        )
        for field, value in {
            'patronymic': patronymic,
            'phone': phone,
            'address': address,
        }.items():
            if not getattr(parent, field):
                setattr(parent, field, value)
        parent.save()
        return parent

    def _pupil(self, password, username, last_name, first_name, patronymic, birth_date, address):
        user = self._user(username, password, first_name, last_name, email='')
        pupil, _ = Pupil.objects.get_or_create(
            user=user,
            defaults={
                'patronymic': patronymic,
                'birth_date': birth_date,
                'address': address,
                'birth_certificate': 'I-АБ 654321, выдан ЗАГС г. Томска, 01.03.2018',
            },
        )
        pupil.patronymic = patronymic
        pupil.birth_date = birth_date
        pupil.address = address
        pupil.save()
        return pupil

    def _course(self, title, code, direction, teachers):
        course, created = Course.objects.get_or_create(
            code=code,
            defaults={
                'title': title,
                'slug': code.lower().replace('_', '-'),
                'direction': direction,
                'is_published': Course.Status.PUBLISHED,
                'description': f'Демо-курс: {title}',
            },
        )
        if course.direction != direction:
            course.direction = direction
            course.save(update_fields=['direction'])
        course.teachers.set(teachers)
        return course

    def _group(self, course, name, teacher, start, end):
        group, _ = Group.objects.get_or_create(
            name=name,
            course=course,
            defaults={
                'teacher': teacher,
                'start_date': start,
                'end_date': end,
                'status': Group.Status.ACTIVE,
                'description': '',
            },
        )
        if group.teacher_id != teacher.pk:
            group.teacher = teacher
            group.save(update_fields=['teacher'])
        return group

    def _enroll(self, pupil, group, date_from):
        Enrollment.objects.get_or_create(
            pupil=pupil,
            group=group,
            defaults={'date_from': date_from},
        )

    def _schedule(self, group, teacher, base_date, weekday, start, end):
        lesson_date = base_date + timedelta(days=1)
        Schedule.objects.get_or_create(
            group=group,
            lesson_date=lesson_date,
            start_time=start,
            defaults={
                'end_time': end,
                'weekday': weekday,
                'teacher': teacher,
                'status': 'approved',
                'room': '101',
            },
        )
