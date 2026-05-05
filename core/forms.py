from django import forms

from accounts.models import Parent
from core.models import CourseReview, Application


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
    first_name = forms.CharField(label='Имя', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Фамилия', required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Parent
        fields = [
            'first_name', 'last_name',
            'phone', 'work_place', 'additional_contacts', 'address', 'passport'
        ]
        labels = {
            'phone': 'Телефон',
            'work_place': 'Место работы',
            'additional_contacts': 'Дополнительные контакты',
            'address': 'Домашний адрес',
            'passport': 'Паспортные данные',
        }
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'work_place': forms.TextInput(attrs={'class': 'form-control'}),
            'additional_contacts': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'passport': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        parent = super().save(commit=False)
        user = parent.user
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
            parent.save()
            self.save_m2m()
        return parent
