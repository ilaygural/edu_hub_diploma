from django.contrib import admin
from .models import Course, Tag

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':("title",)}
    list_display = ['title', 'code', 'slug', 'is_published', 'time_create']
    list_display_links = ('title', 'code')
    list_editable = ('is_published',)
    list_filter = ['is_published']
    search_fields = ['title', 'code']
    ordering = ['-time_create']
    list_per_page = 20

# admin.site.register(Tag)
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':("name",)}
    list_display = ['name', 'slug']