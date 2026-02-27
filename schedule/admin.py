from django.contrib import admin
from django.db.models import Q, Count

from .models import Group, Enrollment, Attendance, Schedule, Payment


# Register your models here.
#  Кастомный фильтр активных учеников в группе
class HasActivePupilsFilter(admin.SimpleListFilter):
    title = "Активные ученики"
    parameter_name = "has_active"

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Есть активные'),
            ('no', 'Нет активных')
        ]

    def queryset(self, request, queryset):
        queryset = queryset.annotate(
            active_count=Count('group_enrollments', filter=Q(group_enrollments__date_to__isnull=True))
        )
        if self.value() == 'yes':
            return queryset.filter(active_count__gt=0)
        elif self.value() == 'no':
            return queryset.filter(active_count=0)
        return queryset


# admin.site.register(Group)
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'start_date', 'end_date']
    list_filter = [HasActivePupilsFilter, 'status']
    search_fields = ['name']


# admin.site.register(Enrollment)
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['pupil', 'group', 'date_from', 'date_to', 'is_active']
    list_filter = ['date_from', 'group']
    search_fields = ['pupil__user__last_name', 'group__name']
    # Убираем N+1 по pupil->user и group
    list_select_related = ('pupil__user', 'group')
    # Не подгружаем весь список вариантов сразу
    autocomplete_fields = ('pupil', 'group')


# admin.site.register(Attendance)
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['pupil', 'lesson_date', 'status']
    list_filter = ['status', 'lesson_date']
    search_fields = ['pupil__user__last_name']
    # Убираем N+1 по pupil->user
    list_select_related = ('pupil__user',)
    autocomplete_fields = ('pupil',)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['group', 'lesson_date', 'start_time', 'end_time', 'teacher']
    list_filter = ['group', 'lesson_date']
    search_fields = ['group__name', 'teacher__user__last_name']
    # Убираем N+1 по group и teacher (и сразу пользователя преподавателя)
    list_select_related = ('group', 'teacher', 'teacher__user')
    autocomplete_fields = ('group', 'teacher')


# admin.site.register(Payment)
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['pupil', 'amount', 'payment_date', 'purpose', 'is_recent']
    list_filter = ['purpose', 'payment_date']
    search_fields = ['pupil__user__last_name']
    # Убираем N+1 по pupil->user
    list_select_related = ('pupil__user',)
    autocomplete_fields = ('pupil',)
