from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Mailing, Message, Recipient

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["subject", "body"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "Тема письма"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 6, "placeholder": "Текст сообщения"}),
        }


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ["email", "full_name", "comment"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class MailingForm(forms.ModelForm):
    # Важно: ManyToMany нужно рендерить как множественный выбор.
    recipients = forms.ModelMultipleChoiceField(
        queryset=Recipient.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        help_text="Выберите получателей из списка (можно несколько)."
    )

    class Meta:
        model = Mailing
        fields = ["creator", "start_time", "end_time", "message", "recipients"]
        # creator мы не показываем в форме — ставим в view
        exclude = ["creator", "status"]

        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "message": forms.Select(attrs={"class": "form-select"}),
        }