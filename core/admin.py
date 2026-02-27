from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Course, Tag, CourseReview


@admin.action(description="Опубликовать выбранные курсы")
def make_published(modeladmin, request, queryset):
    updated = queryset.update(is_published=Course.Status.PUBLISHED)
    modeladmin.message_user(request, f"Опубликовано {updated} курсов")


@admin.action(description="Снять с публикации")
def make_draft(modeladmin, request, queryset):
    updated = queryset.update(is_published=Course.Status.DRAFT)
    modeladmin.message_user(request, f"{updated} курсов сняты с публикации")


#  Кастомный фильтр наличия преподавателя
class HasTeacherFilter(admin.SimpleListFilter):
    title = "Наличие преподавателя"
    parameter_name = "has_teacher"

    def lookups(self, request, model_admin):
        return [("yes", 'Есть преподаватели'),
                ("no", "Нет преподавателей")
                ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(teachers__isnull=False).distinct()
        elif self.value() == "no":
            return queryset.filter(teachers__isnull=True).distinct()
        else:
            return queryset


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    fields = ['title', 'slug', 'code', 'description', 'price', 'is_published', 'tags', 'teachers', 'photo',
              'course_photo']
    readonly_fields = ['time_create', 'time_update', 'course_photo']
    prepopulated_fields = {'slug': ("title",)}
    list_display = ['title', 'code', 'slug', 'is_published', 'short_desc', 'teacher_list', 'course_photo']
    list_display_links = ('title', 'code')
    list_editable = ('is_published',)
    list_filter = [HasTeacherFilter, 'is_published']
    search_fields = ['title', 'code']
    ordering = ['-time_create']
    list_per_page = 20
    actions = [make_published, make_draft]
    save_on_top = True

    # filter_vertical = ['tags']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Префетчим преподавателей вместе с их пользователями и теги, чтобы убрать N+1
        return qs.prefetch_related('teachers__user', 'tags')

    @admin.display(description='Краткое описание')
    def short_desc(self, obj):
        return obj.description[:50] + '...' if obj.description else '-'

    @admin.display(description='Преподаватели')
    def teacher_list(self, obj):
        names = [
            (t.user.get_full_name() or t.user.username) if t.user_id else str(t)
            for t in obj.teachers.all()[:3]
        ]
        return ', '.join(names)

    @admin.display(description="Фото")
    def course_photo(self, course: Course):
        if course.photo:
            return mark_safe(f"<img src='{course.photo.url}' width=50>")
        return "Без фото"


# admin.site.register(Tag)
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("name",)}
    list_display = ['name', 'slug']


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'rating', 'is_published', 'created_at']
    list_filter = ['is_published', 'rating']
    search_fields = ['name', 'email', 'text']
    actions = ['make_published']
    # Подтягиваем FK course одной связкой, чтобы не было N+1 на changelist
    list_select_related = ('course',)

    @admin.action(description='Опубликовать выбранные отзывы')
    def make_published(self, request, queryset):
        queryset.update(is_published=True)
