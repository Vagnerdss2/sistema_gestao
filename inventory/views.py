from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from core.views import AppCreateView, AppDetailView, AppFormPageView, AppListView, AppUpdateView
from inventory.forms import AddStockForm, AssignEmployeeForm, InventoryItemForm
from inventory.models import InventoryItem, MovementType, StockMovement
from organization.models import Employee


class InventoryItemListView(AppListView):
    model = InventoryItem
    template_name = "inventory/item_list.html"
    page_title = "Inventário e Estoque"
    page_description = "Controle de equipamentos, patrimônio, unidades em estoque e vinculação de colaboradores."
    create_url_name = "inventory:item-create"
    update_url_name = "inventory:item-update"
    detail_url_name = "inventory:item-detail"

    def get_queryset(self):
        qs = InventoryItem.objects.select_related("category", "branch", "assigned_employee").order_by("name")
        q = self.request.GET.get("q", "").strip()
        colaborador = self.request.GET.get("colaborador", "").strip()

        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(model__icontains=q)
                | Q(brand__icontains=q)
                | Q(serial_number__icontains=q)
                | Q(asset_tag__icontains=q)
                | Q(category__name__icontains=q)
                | Q(assigned_employee__full_name__icontains=q)
                | Q(assigned_employee__email__icontains=q)
            )

        if colaborador:
            if colaborador.isdigit():
                qs = qs.filter(assigned_employee_id=int(colaborador))
            else:
                qs = qs.filter(
                    Q(assigned_employee__full_name__icontains=colaborador)
                    | Q(assigned_employee__email__icontains=colaborador)
                )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employees"] = Employee.objects.filter(is_active=True).order_by("full_name")
        context["q"] = self.request.GET.get("q", "").strip()
        context["selected_colaborador"] = self.request.GET.get("colaborador", "").strip()
        return context


class InventoryItemCreateView(AppCreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    page_title = "Novo Item de Estoque"
    page_description = "Cadastre um item de estoque ou patrimonio."
    cancel_url_name = "inventory:item-list"
    success_url = reverse_lazy("inventory:item-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.quantity > 0:
            StockMovement.objects.create(
                item=self.object,
                movement_type=MovementType.ENTRY,
                quantity=self.object.quantity,
                reference="Entrada inicial de cadastro",
                notes="Estoque registrado na criação do item.",
            )
        messages.success(self.request, f"Item '{self.object.name}' cadastrado com sucesso!")
        return response


class InventoryItemUpdateView(AppUpdateView):
    model = InventoryItem
    form_class = InventoryItemForm
    page_title = "Editar Item"
    page_description = "Atualize dados de estoque, vinculacao e status."
    cancel_url_name = "inventory:item-list"
    success_url = reverse_lazy("inventory:item-list")


class InventoryItemDetailView(AppDetailView):
    model = InventoryItem
    queryset = InventoryItem.objects.select_related("category", "branch", "assigned_employee").prefetch_related("movements")
    page_title = "Detalhes do Item"
    list_url_name = "inventory:item-list"
    template_name = "inventory/item_detail.html"


class InventoryItemAddStockView(AppFormPageView, FormView):
    form_class = AddStockForm
    template_name = "shared/object_form.html"
    cancel_url_name = "inventory:item-list"
    submit_label = "Adicionar Unidades"

    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(InventoryItem, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Adicionar Unidades ao Estoque: {self.item.name}"
        context["page_description"] = f"Estoque atual: {self.item.quantity} unidade(s)."
        return context

    def form_valid(self, form):
        quantity = form.cleaned_data["quantity"]
        reference = form.cleaned_data.get("reference", "")
        notes = form.cleaned_data.get("notes", "")

        StockMovement.register(
            item=self.item,
            movement_type=MovementType.ENTRY,
            quantity=quantity,
            reference=reference or "Entrada manual de unidades",
            notes=notes,
        )
        messages.success(
            self.request,
            f"Adicionadas {quantity} unidade(s) ao item '{self.item.name}'. Novo total em estoque: {self.item.quantity}.",
        )
        return redirect("inventory:item-list")


class InventoryItemAssignView(AppFormPageView, FormView):
    form_class = AssignEmployeeForm
    template_name = "shared/object_form.html"
    cancel_url_name = "inventory:item-list"
    submit_label = "Vincular e Dar Baixa"

    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(InventoryItem, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Vincular Colaborador e Dar Baixa: {self.item.name}"
        context["page_description"] = f"Estoque disponível para dar baixa: {self.item.quantity} unidade(s)."
        return context

    def form_valid(self, form):
        employee = form.cleaned_data["employee"]
        quantity = form.cleaned_data["quantity"]
        notes = form.cleaned_data.get("notes", "")

        if self.item.quantity < quantity:
            form.add_error(
                "quantity",
                f"Quantidade informada ({quantity}) é superior ao estoque disponível ({self.item.quantity}).",
            )
            return self.form_invalid(form)

        if employee.branch_id != self.item.branch_id:
            self.item.branch = employee.branch

        self.item.assigned_employee = employee
        self.item.save()

        StockMovement.register(
            item=self.item,
            movement_type=MovementType.EXIT,
            quantity=quantity,
            reference=f"Vínculo com colaborador: {employee.full_name}",
            notes=notes,
        )

        messages.success(
            self.request,
            f"Baixa de {quantity} unidade(s) realizada! Item '{self.item.name}' vinculado ao colaborador {employee.full_name}.",
        )
        return redirect("inventory:item-list")
