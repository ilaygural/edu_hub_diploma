from django import forms



#  простая несвязанная форма для обратной связи (на почту)
class CourseQuestionForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label="Ваше имя",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    email = forms.EmailField(
        label='Email для ответа',
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    question = forms.CharField(
        label="Вопрос",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "5"})
    )