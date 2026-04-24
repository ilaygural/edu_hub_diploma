from django.urls import path
from django.views.generic import TemplateView, RedirectView

from . import views

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
]
