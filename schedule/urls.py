from django.urls import path
from . import views

urlpatterns = [
    path('proposal/create/', views.ScheduleProposalCreateView.as_view(), name='schedule_proposal_create'),
    path('proposals/', views.ScheduleProposalListView.as_view(), name='schedule_proposal_list'),
    path('proposal/approve/<int:pk>/', views.approve_proposal, name='approve_proposal'),
    path('proposal/reject/<int:pk>/', views.reject_proposal, name='reject_proposal'),
]
