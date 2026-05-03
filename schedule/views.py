from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import ScheduleProposal
from .forms import ScheduleProposalForm
from django.views.generic import ListView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from core.models import Course
from schedule.models import Group, Schedule
from django.utils import timezone


class ScheduleProposalCreateView(LoginRequiredMixin, CreateView):
    model = ScheduleProposal
    form_class = ScheduleProposalForm
    template_name = 'schedule/proposal_form.html'
    success_url = reverse_lazy('teacher_dashboard')

    def form_valid(self, form):
        form.instance.teacher = self.request.user.teacher_profile
        return super().form_valid(form)


class ScheduleProposalListView(LoginRequiredMixin, ListView):
    model = ScheduleProposal
    template_name = 'schedule/proposal_list.html'
    context_object_name = 'proposals'
    queryset = ScheduleProposal.objects.filter(status='pending')


def approve_proposal(request, pk):
    proposal = get_object_or_404(ScheduleProposal, pk=pk)
    course, _ = Course.objects.get_or_create(title=proposal.course_name)

    def get_next_weekday(weekday_num):
        today = datetime.now().date()
        days_ahead = weekday_num - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    # Маппинг дней недели
    weekday_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5
    }
    group_name_clean = proposal.group_name.strip()
    # Поиск группы по названию и курсу
    group, created = Group.objects.get_or_create(
        name=group_name_clean,
        course=course,
        defaults={
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timezone.timedelta(days=365),
        }
    )

    # Цикл по дням недели
    for weekday_name in [proposal.weekday1, proposal.weekday2]:
        lesson_date = get_next_weekday(weekday_map[weekday_name])
        Schedule.objects.create(
            group=group,
            lesson_date=lesson_date,
            start_time=proposal.start_time,
            end_time=proposal.end_time,
            room=proposal.room,
            teacher=proposal.teacher,
            status='approved'
        )

    proposal.status = 'approved'
    proposal.save()
    return redirect('schedule_proposal_list')


def reject_proposal(request, pk):
    proposal = get_object_or_404(ScheduleProposal, pk=pk)
    proposal.status = 'rejected'
    proposal.save()
    messages.warning(request, 'Предложение отклонено.')
    return redirect('schedule_proposal_list')

