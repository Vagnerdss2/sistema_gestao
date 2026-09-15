from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import FormView

from core.views import AppFormPageView
from accounts.forms import RegistrationForm
from organization.models import Employee

User = get_user_model()

class RegisterView(AppFormPageView):
    """
    View para o cadastro de novos usuários e colaboradores.
    Implementa a criação atômica de User e Employee.
    """
    template_name = "accounts/register.html"
    form_class = RegistrationForm
    page_title = "Cadastro de Usuário"
    page_description = "Crie sua conta de acesso ao sistema vinculando-a ao seu registro de colaborador."
    submit_label = "Cadastrar Conta"
    cancel_url_name = "accounts:login"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        """
        Sobrescreve o salvamento para criar atomicamente o User e o Employee.
        """
        data = form.cleaned_data

        try:
            with transaction.atomic():
                # 1. Cria o usuário de autenticação do Django
                user = User.objects.create_user(
                    username=data["username"],
                    email=data["email"],
                    password=data["password"],
                    first_name=data["full_name"].split(" ")[0] if data["full_name"] else "",
                    last_name=" ".join(data["full_name"].split(" ")[1:]) if data["full_name"] else "",
                )

                # 2. Cria o colaborador vinculado ao usuário
                Employee.objects.create(
                    user=user,
                    full_name=data["full_name"],
                    email=data["email"],
                    department=data["department"],
                    branch=data["branch"],
                    job_title="Não Informado", # Valor padrão inicial
                )

                messages.success(self.request, "Conta criada com sucesso! Você já pode fazer login.")
        except Exception as e:
            messages.error(self.request, f"Ocorreu um erro ao criar a conta: {str(e)}")
            return self.form_invalid(form)

        return super().form_valid(form)
