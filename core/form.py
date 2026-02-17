from django import forms


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
