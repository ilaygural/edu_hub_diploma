from django.contrib import admin
from .models import Pupil, Teacher, Parent


# Register your models here.
admin.site.register(Pupil)
admin.site.register(Teacher)
admin.site.register(Parent)