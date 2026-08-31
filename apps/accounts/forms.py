from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class EmailAuthenticationForm(auth_forms.AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email'}),
    )

    error_messages = {
        **auth_forms.AuthenticationForm.error_messages,
        'invalid_login': (
            'Please enter a correct email and password. Note that both fields may be case-sensitive.'
        ),
    }


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists')
        return email


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label='Email address')


class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(
        label='New password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', 'The two password fields didn’t match.')

        return cleaned_data


class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'avatar', 'phone_number', 'bio')
