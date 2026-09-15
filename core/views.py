from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Count, F, Q, Sum
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from inventory.models import InventoryItem, InventoryStatus
from kanban.models import KanbanTask, TaskStatus
from supportdesk.models import ServiceOrder


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    View principal do Painel de Controle (Dashboard).
    
    Reúne e calcula as métricas operacionais consolidadas do sistema em tempo real:
    - Estoque geral disponível e valor financeiro total dos itens.
    - Quantidade de equipamentos atualmente em uso com colaboradores (Inventário).
    - Alertas de itens com estoque no nível crítico ou abaixo do mínimo.
    - Total de atendimentos/ordens de serviço executadas no mês atual agrupadas por filial e setor.
    - Tarefas do quadro Kanban pendentes e atrasadas em relação ao prazo estipulado.
    - Lista dos últimos atendimentos de suporte registrados para acompanhamento rápido.
    """

    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_month = timezone.localdate().month

        # Agregações de estoque e inventário
        inventory_totals = InventoryItem.objects.aggregate(
            # Total de unidades físicas disponíveis no estoque (sem colaborador vinculado)
            total_in_stock=Sum("quantity", filter=Q(status=InventoryStatus.IN_STOCK, assigned_employee__isnull=True)),
            # Total de unidades de equipamentos atualmente em uso por colaboradores
            total_in_use=Sum("quantity", filter=Q(assigned_employee__isnull=False) | Q(status=InventoryStatus.IN_USE)),
            # Quantidade de itens que atingiram ou estão abaixo do estoque mínimo configurado
            low_stock=Count("id", filter=Q(assigned_employee__isnull=True, quantity__lte=models.F("minimum_quantity"))),
            # Valor financeiro monetário total do estoque disponível (quantidade * preço unitário)
            stock_value=Sum(
                F("quantity") * F("unit_price"),
                filter=Q(assigned_employee__isnull=True, status=InventoryStatus.IN_STOCK),
                output_field=models.DecimalField(),
            ),
        )

        # Resumo de serviços do mês agrupados por Filial e Setor atendidos
        service_summary = (
            ServiceOrder.objects.filter(service_datetime__month=current_month)
            .values("branch__name", "department__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:8]
        )

        # Total geral de atendimentos no mês atual
        total_services_month = ServiceOrder.objects.filter(service_datetime__month=current_month).count()

        # Alimenta as variáveis que serão renderizadas no template do Dashboard
        context.update(
            {
                "inventory_totals": inventory_totals,
                "total_services_month": total_services_month,
                # Tarefas com prazo vencido e que ainda não foram marcadas como concluídas
                "overdue_tasks": KanbanTask.objects.filter(
                    due_date__lt=timezone.localdate(),
                )
                .exclude(status=TaskStatus.DONE)
                .count(),
                # Total de tarefas em andamento, a fazer ou aguardando
                "open_tasks": KanbanTask.objects.exclude(status=TaskStatus.DONE).count(),
                # Últimas 5 ordens de serviço registradas
                "recent_service_orders": ServiceOrder.objects.select_related(
                    "attended_user", "branch", "department", "technician"
                )[:5],
                "service_summary": service_summary,
                # Itens de estoque que necessitam de reposição imediata
                "low_stock_items": InventoryItem.objects.filter(
                    assigned_employee__isnull=True,
                    quantity__lte=models.F("minimum_quantity"),
                )
                .exclude(status=InventoryStatus.DISCARDED)
                .select_related("category", "branch")
                .order_by("quantity", "name")[:8],
            }
        )
        return context


class AppListView(LoginRequiredMixin, ListView):
    """
    Classe base genérica para telas de listagem (Read/List) de entidades do sistema.
    
    Padroniza títulos, descrições e links de navegação para CRUDs (Criar, Editar, Detalhes, Excluir),
    exigindo autenticação do usuário logado.
    """

    template_name = "shared/object_list.html"
    context_object_name = "objects"
    page_title = ""
    page_description = ""
    create_url_name = ""
    update_url_name = ""
    detail_url_name = ""
    delete_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Injeta as variáveis de cabeçalho e rotas no contexto do template compartilhado
        context.update(
            {
                "page_title": self.page_title,
                "page_description": self.page_description,
                "create_url_name": self.create_url_name,
                "update_url_name": self.update_url_name,
                "detail_url_name": self.detail_url_name,
                "delete_url_name": self.delete_url_name,
            }
        )
        return context


class AppCreateView(LoginRequiredMixin, CreateView):
    """
    Classe base genérica para telas de criação de registros (Create).
    
    Padroniza título, botões de ação e cancelamento para os formulários de cadastro.
    """

    template_name = "shared/object_form.html"
    page_title = ""
    page_description = ""
    submit_label = "Salvar"
    cancel_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": self.page_title,
                "page_description": self.page_description,
                "submit_label": self.submit_label,
                "cancel_url_name": self.cancel_url_name,
            }
        )
        return context


class AppUpdateView(LoginRequiredMixin, UpdateView):
    """
    Classe base genérica para telas de edição/atualização de registros (Update).
    
    Padroniza o título e o formulário de alteração de dados de qualquer entidade.
    """

    template_name = "shared/object_form.html"
    page_title = ""
    page_description = ""
    submit_label = "Atualizar"
    cancel_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": self.page_title,
                "page_description": self.page_description,
                "submit_label": self.submit_label,
                "cancel_url_name": self.cancel_url_name,
            }
        )
        return context


class AppDeleteView(LoginRequiredMixin, DeleteView):
    """
    Classe base genérica para telas de confirmação de exclusão (Delete).
    
    Exibe um modal/página de confirmação antes de remover definitivamente um registro do banco.
    """

    template_name = "shared/object_confirm_delete.html"
    page_title = "Excluir Registro"
    page_description = "Confirme se realmente deseja excluir este registro."
    submit_label = "Confirmar Exclusão"
    cancel_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": self.page_title,
                "page_description": self.page_description,
                "submit_label": self.submit_label,
                "cancel_url_name": self.cancel_url_name,
            }
        )
        return context


class AppDetailView(LoginRequiredMixin, DetailView):
    """
    Classe base genérica para telas de visualização detalhada (Read/Detail).
    
    Apresenta todos os atributos e relacionamentos de uma única entidade selecionada.
    """

    template_name = "shared/object_detail.html"
    page_title = ""
    list_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": self.page_title,
                "list_url_name": self.list_url_name,
            }
        )
        return context


class AppFormPageView(LoginRequiredMixin, TemplateView):
    """
    Classe base para páginas de formulários customizados ou compostos (FormView/Formsets).
    
    Fornece autenticação obrigatória e variáveis de contexto padronizadas para formulários operacionais.
    """

    page_title = ""
    page_description = ""
    submit_label = "Salvar"
    cancel_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": self.page_title,
                "page_description": self.page_description,
                "submit_label": self.submit_label,
                "cancel_url_name": self.cancel_url_name,
            }
        )
        context.update(kwargs)
        return context

