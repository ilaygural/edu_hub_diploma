from django.urls import path, include
from django.views.generic import TemplateView, RedirectView

from . import views
from .views import TeacherGroupDetailView, TeacherLessonView

urlpatterns = [
    # path('', views.HomeView.as_view(), name='home'),
    path('', RedirectView.as_view(url='/users/role-select/'), name='home'),
    # Courses
    path('courses/', views.CourseListView.as_view(), name='courses'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<slug:slug>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('courses/<slug:slug>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),

    # Teachers
    path('teachers/', views.TeacherListView.as_view(), name='teachers'),

    # Other pages
    path('schedule/', views.schedule, name='schedule'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('application/create/', views.ApplicationCreateView.as_view(), name='application_create'),
    path('application/done/', TemplateView.as_view(template_name='core/application_done.html'),
         name='application_done'),

    # Tags, questions, reviews (оставляем как есть)
    path('tag/<slug:tag_slug>/', views.courses_by_tag, name='courses_by_tag'),
    path('course/<int:course_id>/ask/', views.AskQuestionView.as_view(), name='ask_question'),
    path('course/<int:course_id>/review/', views.AddReviewView.as_view(), name='add_review'),
    path('parent/dashboard/', views.ParentDashboardView.as_view(), name='parent_dashboard'),
    path('teacher/dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('manager/dashboard/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('application/approve/<int:pk>/', views.approve_application, name='approve_application'),
    path('application/reject/<int:pk>/', views.reject_application, name='reject_application'),
    path('expel/pupil/<int:pupil_id>/', views.expel_pupil, name='expel_pupil'),
    path('manager/applications/', views.manager_applications, name='manager_applications'),
    path('manager/pupils/', views.manager_pupils, name='manager_pupils'),
    path(
        'manager/pupils/<int:pupil_id>/contract/',
        views.manager_pupil_contract,
        name='manager_pupil_contract',
    ),
    path('manager/groups/', views.manager_groups, name='manager_groups'),
    path('manager/schedule/', views.manager_schedule, name='manager_schedule'),
    path('manager/payments/', views.manager_payments, name='manager_payments'),
    path('manager/reports/', views.manager_reports, name='manager_reports'),
    path('manager/applications/', views.manager_applications, name='manager_applications'),
    path('manager/pupils/', views.manager_pupils, name='manager_pupils'),
    path('schedule/', include('schedule.urls')),
    path('save-attendance/', views.save_attendance, name='save_attendance'),
    path('teacher/group/<int:pk>/', TeacherGroupDetailView.as_view(), name='teacher_group_detail'),
    path('teacher/lesson/<int:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('teacher/journal/', views.TeacherJournalView.as_view(), name='teacher_journal'),
    path('teacher/ktp/', views.TeacherKTPGenerateView.as_view(), name='teacher_ktp'),
    path('teacher/lesson/<int:pk>/', TeacherLessonView.as_view(), name='teacher_lesson'),
    path('parent/profile/edit/', views.ParentContractEditView.as_view(), name='parent_profile_edit'),
    path('parent/messages/', views.parent_messages, name='parent_messages'),
    path('parent/messages/new/', views.parent_message_compose, name='parent_message_compose'),
    path('parent/messages/<int:thread_id>/', views.parent_message_thread, name='parent_message_thread'),
    path('teacher/messages/', views.teacher_messages, name='teacher_messages'),
    path('teacher/messages/new/', views.teacher_message_compose, name='teacher_message_compose'),
    path('teacher/messages/<int:thread_id>/', views.teacher_message_thread, name='teacher_message_thread'),

]
