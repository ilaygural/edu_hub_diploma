from django.contrib import admin
from .models import Group, Enrollment, Attendance, Schedule, Payment


# Register your models here.
# admin.site.register(Group)
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'start_date', 'end_date']
    list_filter = ['status']
    search_fields = ['name']


# admin.site.register(Enrollment)
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['pupil', 'group', 'date_from', 'date_to', 'is_active']
    list_filter = ['date_from', 'group']
    search_fields = ['pupil__user__last_name', 'group__name']


# admin.site.register(Attendance)
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['pupil', 'lesson_date', 'status']
    list_filter = ['status', 'lesson_date']
    search_fields = ['pupil__user__last_name']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['group', 'lesson_date', 'start_time', 'end_time', 'teacher']
    list_filter = ['group', 'lesson_date']
    search_fields = ['pupil__user__last_name', 'group__name']


# admin.site.register(Payment)
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['pupil', 'amount', 'payment_date', 'purpose', 'is_recent']
    list_filter = ['purpose', 'payment_date']
    search_fields = ['pupil__user__last_name']
