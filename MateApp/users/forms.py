from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={'placeholder': 'Tu nombre'}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Apellido',
        widget=forms.TextInput(attrs={'placeholder': 'Tu apellido'}),
    )
    cedula = forms.CharField(
        max_length=20,
        required=False,
        label='Cedula',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 1717171717'}),
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'cedula', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user
