from django import forms
from .models import ScheduleProposal, Schedule

class ScheduleProposalForm(forms.ModelForm):
    class Meta:
        model = ScheduleProposal
        fields = ['course_name', 'group_name', 'weekday1', 'weekday2', 'start_time', 'end_time', 'room']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'course_name': 'Название направления',
            'group_name': 'Название группы',
            'weekday1': 'Первый день недели',
            'weekday2': 'Второй день недели',
            'start_time': 'Время начала',
            'end_time': 'Время окончания',
            'room': 'Кабинет',
        }