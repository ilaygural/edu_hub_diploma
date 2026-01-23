from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses_list, name='courses'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<slug:slug>/', views.course_detail_by_slug, name='course_by_slug'),
]
