from django import forms
from core.forms import StyledForm
from django.core.exceptions import ValidationError
from organization.models import Department, Branch

class RegistrationForm(StyledForm):
    """
    Formulário de cadastro de novo usuário e colaborador.
    Coleta dados de autenticação e dados profissionais básicos.
    """
    full_name = forms.CharField("Nome Completo", max_length=150, widget=forms.TextInput(attrs={"placeholder": "Digite seu nome completo"}))
    username = forms.CharField("Login", max_length=150, widget=forms.TextInput(attrs={"placeholder": "Escolha um nome de usuário"}))
    email = forms.EmailField("E-mail", max_length=254, widget=forms.EmailInput(attrs={"placeholder": "exemplo@email.com"}))
    password = forms.CharField("Senha", widget=forms.PasswordInput(attrs={"placeholder": "********"}))
    password_confirm = forms.CharField("Confirmar Senha", widget=forms.PasswordInput(attrs={"placeholder": "********"}))

    department = forms.ModelChoiceField(
        "Setor",
        queryset=Department.objects.all(),
        widget=forms.Select(attrs={"placeholder": "Selecione o setor"})
    )
    branch = forms.ModelChoiceField(
        "Filial",
        queryset=Branch.objects.all(),
        widget=forms.Select(attrs={"placeholder": "Selecione a filial"})
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Este login já está em uso. Por favor, escolha outro.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este e-mail já está vinculado a uma conta.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "As senhas não coincidem.")

        return cleaned_data
