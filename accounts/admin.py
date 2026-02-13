from django.contrib import admin
from .models import Pupil, Teacher, Parent
from datetime import date


# Register your models here.
# admin.site.register(Pupil)
@admin.register(Pupil)
class PupilAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_email', 'status', 'enrolled_date', 'age']
    list_filter = ['status']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

    @admin.display(description='Возраст')
    def age(self, obj):
        if obj.birth_date:
            return date.today().year - obj.birth_date.year
        return '-'


# admin.site.register(Teacher)
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'specialization', 'experience_years', 'is_active']
    list_filter = ['is_active', 'specialization']
    search_fields = ['user__first_name', 'user__last_name']


# admin.site.register(Parent)
@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'phone', 'work_place']
    search_fields = ['user__first_name', 'user__last_name']
    filter_horizontal = ['children']
