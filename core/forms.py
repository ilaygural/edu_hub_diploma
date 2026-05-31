from django import forms
from django.utils import timezone

from accounts.models import Parent, Pupil, Teacher
from core.models import CourseReview, Application
from schedule.models import Group, Schedule


#  простая несвязанная форма для обратной связи (на почту)
class CourseQuestionForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        min_length=2,
        error_messages={
            'required': 'Пожалуйста, представьтесь',  # твоё сообщение
            'min_length': 'Имя должно быть не короче 2 символов',
        },
        label="Ваше имя",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    email = forms.EmailField(
        label='Email для ответа',
        help_text='Укажите действующий email, мы ответим вам',
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    question = forms.CharField(
        label="Вопрос",
        help_text='Опишите ваш вопрос максимально подробно',
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "5"})
    )

    def clean_question(self):
        question = self.cleaned_data['question']
        forbidden = ['http', 'www.', 'спам', 'реклама', 'бесплатно']
        lower_question = question.lower()
        for word in forbidden:
            if word in lower_question:
                raise forms.ValidationError(
                    f'В вопросе не должно быть ссылок или слова "{word}"'
                )

        return question


class ReviewForm(forms.ModelForm):
    class Meta:
        model = CourseReview
        fields = ['name', 'email', 'text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_authenticated:
            self.fields['name'].initial = self.user.get_full_name() or self.user.username
            self.fields['email'].initial = self.user.email
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['name'].required = False
            self.fields['email'].required = False


class UploadFileForm(forms.Form):
    file = forms.FileField(label="Выберите файл")


class KTPGenerationForm(forms.Form):
    """Форма генерации каркаса КТП для педагога."""

    date_from = forms.DateField(
        label='Начало полугодия',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    date_to = forms.DateField(
        label='Конец полугодия',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    weekdays = forms.MultipleChoiceField(
        label='Дни недели занятий',
        choices=Schedule.WEEKDAYS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )
    group = forms.ModelChoiceField(
        label='Группа (необязательно)',
        queryset=Group.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    half_year = forms.ChoiceField(
        label='Полугодие',
        choices=[
            ('1', '1 полугодие'),
            ('2', '2 полугодие'),
            ('both', 'Оба полугодия'),
        ],
        initial='1',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from_2 = forms.DateField(
        label='Начало 2-го полугодия',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    date_to_2 = forms.DateField(
        label='Конец 2-го полугодия',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    weekday_slot_1 = forms.CharField(
        label='Первый день недели (шапка КТП)',
        required=False,
        initial='Понедельник (10:30 - 12:00)',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    weekday_slot_2 = forms.CharField(
        label='Второй день недели (шапка КТП)',
        required=False,
        initial='Четверг (10:00 - 11:30)',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    skip_holidays = forms.BooleanField(
        label='Пропускать официальные праздники РФ',
        required=False,
        initial=True,
    )

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher is not None:
            self.fields['group'].queryset = Group.objects.filter(teacher=teacher).select_related('course')

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get('date_from')
        date_to = cleaned.get('date_to')
        weekdays = cleaned.get('weekdays') or []
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Дата начала не может быть позже даты окончания.')
        if not weekdays:
            raise forms.ValidationError('Выберите хотя бы один день недели.')
        if len(weekdays) != 2:
            raise forms.ValidationError(
                'Для Excel-шаблона КТП выберите ровно два дня недели '
                '(левый и правый столбец таблицы).'
            )
        half_year = cleaned.get('half_year')
        if half_year == 'both':
            date_from_2 = cleaned.get('date_from_2')
            date_to_2 = cleaned.get('date_to_2')
            if not date_from_2 or not date_to_2:
                raise forms.ValidationError(
                    'Для двух полугодий укажите даты начала и конца второго полугодия.'
                )
            if date_from_2 > date_to_2:
                raise forms.ValidationError(
                    'Дата начала 2-го полугодия не может быть позже даты окончания.'
                )
        return cleaned


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['course', 'child_name', 'child_age', 'parent_name', 'parent_phone', 'parent_email']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'child_name': forms.TextInput(attrs={'class': 'form-control'}),
            'child_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class ParentProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Имя',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label='Фамилия',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Parent
        fields = [
            'representative_relation',
            'patronymic',
            'phone',
            'address',
            'snils',
            'passport_series',
            'passport_number',
            'passport_issued_by',
            'passport_issued_date',
            'passport',
            'work_place',
            'additional_contacts',
        ]
        widgets = {
            'representative_relation': forms.Select(attrs={'class': 'form-select'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'snils': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000-000-000 00'}),
            'passport_series': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_issued_by': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_issued_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'passport': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'work_place': forms.TextInput(attrs={'class': 'form-control'}),
            'additional_contacts': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        parent = super().save(commit=False)
        user = parent.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            parent.save()
            self.save_m2m()
        return parent


class PupilContractForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Имя',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label='Фамилия',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Pupil
        fields = [
            'patronymic',
            'birth_date',
            'place_of_birth',
            'pfdo_certificate_number',
            'identity_document_type',
            'birth_certificate',
            'passport_series',
            'passport_number',
            'passport_issued_by',
            'passport_issued_date',
            'snils',
            'phone',
            'address',
        ]
        widgets = {
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'place_of_birth': forms.TextInput(attrs={'class': 'form-control'}),
            'pfdo_certificate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'identity_document_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'birth_certificate': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'passport_series': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_issued_by': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_issued_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'snils': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['pfdo_certificate_number'].required = False
        self.fields['birth_certificate'].help_text = (
            'Серия, номер, кем и когда выдано (для договора и ПФДО)'
        )

    def clean(self):
        cleaned = super().clean()
        doc_type = cleaned.get('identity_document_type')
        if doc_type == Pupil.IdentityDocument.BIRTH_CERTIFICATE:
            if not cleaned.get('birth_certificate', '').strip():
                self.add_error(
                    'birth_certificate',
                    'Укажите данные свидетельства о рождении (п. 2.5 договора).',
                )
        elif doc_type == Pupil.IdentityDocument.PASSPORT:
            if not cleaned.get('passport_series', '').strip() or not cleaned.get('passport_number', '').strip():
                self.add_error(
                    'passport_number',
                    'Укажите серию и номер паспорта ребёнка.',
                )
        return cleaned

    def save(self, commit=True):
        pupil = super().save(commit=False)
        user = pupil.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            pupil.save()
        return pupil


class ParentNewMessageForm(forms.Form):
    pupil = forms.ModelChoiceField(
        label='Ребёнок',
        queryset=Pupil.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    teacher = forms.ModelChoiceField(
        label='Педагог',
        queryset=Teacher.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    body = forms.CharField(
        label='Сообщение',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
    )

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        pupils = parent.children.select_related('user').all()
        self.fields['pupil'].queryset = pupils
        self.fields['pupil'].label_from_instance = lambda p: p.fio
        teacher_ids: set[int] = set()
        from core.messaging import teachers_for_parent_pupil

        for pupil in pupils:
            for teacher in teachers_for_parent_pupil(parent, pupil):
                teacher_ids.add(teacher.pk)
        teachers_qs = Teacher.objects.filter(pk__in=teacher_ids).select_related('user')
        self.fields['teacher'].queryset = teachers_qs
        self.fields['teacher'].label_from_instance = lambda t: t.name_for_parent

    def clean(self):
        cleaned = super().clean()
        pupil = cleaned.get('pupil')
        teacher = cleaned.get('teacher')
        if pupil and teacher:
            from core.messaging import teachers_for_parent_pupil

            allowed = {t.pk for t in teachers_for_parent_pupil(self.parent, pupil)}
            if teacher.pk not in allowed:
                self.add_error('teacher', 'Этот педагог не ведёт активные группы выбранного ребёнка.')
        return cleaned


class TeacherNewMessageForm(forms.Form):
    pupil = forms.ModelChoiceField(
        label='Ученик',
        queryset=Pupil.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    body = forms.CharField(
        label='Сообщение',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
    )

    def __init__(self, teacher, *args, pupil_for_parent_choice=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher
        from core.messaging import parents_for_teacher_pupil, pupils_for_teacher

        pupils_qs = pupils_for_teacher(teacher)
        self.fields['pupil'].queryset = pupils_qs
        self.fields['pupil'].label_from_instance = lambda p: p.fio

        if pupil_for_parent_choice:
            parents = parents_for_teacher_pupil(teacher, pupil_for_parent_choice)
            if len(parents) > 1:
                parents_qs = Parent.objects.filter(
                    pk__in=[p.pk for p in parents],
                ).select_related('user')
                self.fields['parent'] = forms.ModelChoiceField(
                    label='Родитель',
                    queryset=parents_qs,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    help_text='У этого ученика в системе несколько родителей — выберите получателя.',
                )
                self.fields['parent'].label_from_instance = lambda p: p.fio

    def clean(self):
        cleaned = super().clean()
        pupil = cleaned.get('pupil')
        if not pupil:
            return cleaned

        from core.messaging import parents_for_teacher_pupil

        parents = parents_for_teacher_pupil(self.teacher, pupil)
        if not parents:
            self.add_error(
                'pupil',
                'У ученика нет привязанного родителя. Оформите заявку и привязку в системе.',
            )
            return cleaned

        if len(parents) == 1:
            cleaned['parent'] = parents[0]
        else:
            parent = cleaned.get('parent')
            if not parent:
                self.add_error(
                    'parent',
                    'Выберите родителя — у ученика их несколько.',
                )
            else:
                cleaned['parent'] = parent
        return cleaned


class MessageReplyForm(forms.Form):
    body = forms.CharField(
        label='Ответ',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )


class KomplektovanieForm(forms.Form):
    report_date = forms.DateField(
        label='Дата среза',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.localdate,
    )
