from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from inventory.models import InventoryItem, InventoryStatus
from kanban.models import KanbanTask, TaskStatus
from procurement.models import PurchaseOrder, PurchaseStatus
from supportdesk.models import ServiceOrder


class DashboardView(LoginRequiredMixin, TemplateView):
    """Painel operacional com indicadores principais."""

    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_month = timezone.localdate().month

        inventory_totals = InventoryItem.objects.aggregate(
            total_in_stock=Sum("quantity", filter=Q(status=InventoryStatus.IN_STOCK)),
            total_in_use=Count("id", filter=Q(status=InventoryStatus.IN_USE)),
            low_stock=Count("id", filter=Q(quantity__lte=models.F("minimum_quantity"))),
        )

        service_summary = (
            ServiceOrder.objects.filter(service_datetime__month=current_month)
            .values("branch__name", "department__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:8]
        )

        context.update(
            {
                "inventory_totals": inventory_totals,
                "pending_deliveries": PurchaseOrder.objects.filter(
                    status__in=[PurchaseStatus.APPROVED, PurchaseStatus.PURCHASED]
                ).count(),
                "overdue_tasks": KanbanTask.objects.filter(
                    due_date__lt=timezone.localdate(),
                )
                .exclude(status=TaskStatus.DONE)
                .count(),
                "open_tasks": KanbanTask.objects.exclude(status=TaskStatus.DONE).count(),
                "recent_service_orders": ServiceOrder.objects.select_related(
                    "attended_user", "branch", "department", "technician"
                )[:5],
                "service_summary": service_summary,
                "low_stock_items": InventoryItem.objects.filter(
                    quantity__lte=models.F("minimum_quantity")
                )
                .select_related("category", "branch")
                .order_by("quantity", "name")[:8],
            }
        )
        return context


class AppListView(LoginRequiredMixin, ListView):
    """Lista padronizada para CRUDs do sistema."""

    template_name = "shared/object_list.html"
    context_object_name = "objects"
    page_title = ""
    page_description = ""
    create_url_name = ""
    update_url_name = ""
    detail_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": self.page_title,
                "page_description": self.page_description,
                "create_url_name": self.create_url_name,
                "update_url_name": self.update_url_name,
                "detail_url_name": self.detail_url_name,
            }
        )
        return context


class AppCreateView(LoginRequiredMixin, CreateView):
    """Formulario padronizado para criacao."""

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
    """Formulario padronizado para edicao."""

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


class AppDetailView(LoginRequiredMixin, DetailView):
    """Tela padrao de detalhamento."""

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
    """Pagina autenticada para formularios compostos por formsets."""

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
