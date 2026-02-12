from django.contrib import admin
from .models import Course, Tag

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':("title",)}
    list_display = ['title', 'code', 'slug']

admin.site.register(Tag)