from django.contrib import admin
from .models import Group, Enrollment, Attendance, Schedule, Payment


# Register your models here.
admin.site.register(Group)
admin.site.register(Enrollment)
admin.site.register(Attendance)
admin.site.register(Schedule)
admin.site.register(Payment)
