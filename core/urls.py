from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses_list, name='courses'),
    path('courses/<slug:slug>/', views.course_detail_by_slug, name='course_by_slug'),
    # path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('teachers/', views.teachers, name='teachers'),
    path('schedule/', views.schedule, name='schedule'),
    path('about/', views.about, name='about'),
    path('kpi/', views.kpi_dashboard, name='kpi_dashboard'),
    path('course/<slug:course_slug>/', views.course_detail, name='course_detail'),
    path('course/', views.courses_list, name='courses_list'),
    path('tag/<slug:tag_slug>/', views.courses_by_tag, name='courses_by_tag'),
    path('course/<int:course_id>/ask/', views.ask_course_question, name='ask_question'),
]
