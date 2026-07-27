from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import FormView

from core.views import AppCreateView, AppDeleteView, AppDetailView, AppFormPageView, AppListView, AppUpdateView
from inventory.forms import AddStockForm, AssignEmployeeForm, InventoryItemForm, ReturnStockForm
from inventory.models import InventoryItem, InventoryStatus, MovementType, StockMovement
from organization.models import Employee


class InventoryItemListView(AppListView):
    model = InventoryItem
    template_name = "inventory/item_list.html"
    page_title = "Inventário e Estoque"
    page_description = "Controle de equipamentos, patrimônio, unidades em estoque e vinculação de colaboradores."
    create_url_name = "inventory:item-create"
    update_url_name = "inventory:item-update"
    detail_url_name = "inventory:item-detail"
    delete_url_name = "inventory:item-delete"

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


class InventoryItemDeleteView(AppDeleteView):
    model = InventoryItem
    page_title = "Excluir Item de Estoque"
    page_description = "Tem certeza que deseja remover este item de estoque do sistema?"
    cancel_url_name = "inventory:item-list"
    success_url = reverse_lazy("inventory:item-list")

    def form_valid(self, form):
        item_name = str(self.object)
        response = super().form_valid(form)
        messages.success(self.request, f"Item '{item_name}' excluído com sucesso!")
        return response


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

        with transaction.atomic():
            source_item = InventoryItem.objects.select_for_update().get(pk=self.item.pk)

            if source_item.quantity < quantity:
                form.add_error(
                    "quantity",
                    f"Quantidade informada ({quantity}) é superior ao estoque disponível ({source_item.quantity}).",
                )
                return self.form_invalid(form)

            # Unique serialized asset
            if (source_item.serial_number or source_item.asset_tag) and source_item.quantity == 1:
                source_item.assigned_employee = employee
                source_item.status = InventoryStatus.IN_USE
                if employee.branch_id != source_item.branch_id:
                    source_item.branch = employee.branch
                source_item.save()

                StockMovement.objects.create(
                    item=source_item,
                    movement_type=MovementType.EXIT,
                    quantity=1,
                    reference=f"Vínculo com colaborador: {employee.full_name}",
                    notes=notes,
                )
            else:
                # Pool item: deduct quantity from pool, create/update assigned IN_USE item entry
                source_item.quantity -= quantity
                source_item.save(update_fields=["quantity", "updated_at"])

                StockMovement.objects.create(
                    item=source_item,
                    movement_type=MovementType.EXIT,
                    quantity=quantity,
                    reference=f"Baixa por entrega ao colaborador: {employee.full_name}",
                    notes=notes,
                )

                assigned_item = InventoryItem.objects.filter(
                    name=source_item.name,
                    category=source_item.category,
                    brand=source_item.brand,
                    model=source_item.model,
                    branch=employee.branch,
                    assigned_employee=employee,
                    status=InventoryStatus.IN_USE,
                    serial_number="",
                    asset_tag="",
                ).first()

                if assigned_item:
                    assigned_item.quantity += quantity
                    if notes:
                        assigned_item.notes = (assigned_item.notes + "\n" + notes).strip()
                    assigned_item.save(update_fields=["quantity", "notes", "updated_at"])
                else:
                    assigned_item = InventoryItem.objects.create(
                        name=source_item.name,
                        category=source_item.category,
                        brand=source_item.brand,
                        model=source_item.model,
                        serial_number="",
                        asset_tag="",
                        status=InventoryStatus.IN_USE,
                        quantity=quantity,
                        minimum_quantity=0,
                        branch=employee.branch,
                        assigned_employee=employee,
                        notes=notes or f"Vinculado ao colaborador em {timezone.localdate().strftime('%d/%m/%Y')}",
                    )

                StockMovement.objects.create(
                    item=assigned_item,
                    movement_type=MovementType.ENTRY,
                    quantity=quantity,
                    reference=f"Item vinculado ao colaborador: {employee.full_name}",
                    notes=notes,
                )

        messages.success(
            self.request,
            f"Baixa de {quantity} unidade(s) efetuada! O item agora aparece na aba Estoque vinculado ao colaborador {employee.full_name}.",
        )
        return redirect("inventory:item-list")


class InventoryItemReturnStockView(AppFormPageView, FormView):
    form_class = ReturnStockForm
    template_name = "shared/object_form.html"
    cancel_url_name = "inventory:item-list"
    submit_label = "Devolver ao Estoque"

    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(InventoryItem, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emp_name = self.item.assigned_employee.full_name if self.item.assigned_employee else "Colaborador"
        context["page_title"] = f"Devolver ao Estoque: {self.item.name}"
        context["page_description"] = f"Quantidade vinculada a {emp_name}: {self.item.quantity} unidade(s)."
        return context

    def form_valid(self, form):
        quantity = form.cleaned_data["quantity"]
        notes = form.cleaned_data.get("notes", "")

        with transaction.atomic():
            assigned_item = InventoryItem.objects.select_for_update().get(pk=self.item.pk)

            if quantity > assigned_item.quantity:
                form.add_error(
                    "quantity",
                    f"Quantidade a devolver ({quantity}) é superior à quantidade vinculada ({assigned_item.quantity}).",
                )
                return self.form_invalid(form)

            emp_name = assigned_item.assigned_employee.full_name if assigned_item.assigned_employee else "Colaborador"

            assigned_item.quantity -= quantity
            if assigned_item.quantity <= 0:
                assigned_item.delete()
            else:
                assigned_item.save(update_fields=["quantity", "updated_at"])

            pool_item, _ = InventoryItem.objects.get_or_create(
                name=assigned_item.name,
                category=assigned_item.category,
                brand=assigned_item.brand,
                model=assigned_item.model,
                branch=assigned_item.branch,
                assigned_employee=None,
                status=InventoryStatus.IN_STOCK,
                defaults={
                    "quantity": 0,
                    "minimum_quantity": 0,
                    "notes": "Estoque geral unificado",
                },
            )
            pool_item.quantity += quantity
            pool_item.save(update_fields=["quantity", "updated_at"])

            StockMovement.objects.create(
                item=pool_item,
                movement_type=MovementType.ENTRY,
                quantity=quantity,
                reference=f"Devolução de estoque do colaborador: {emp_name}",
                notes=notes,
            )

        messages.success(
            self.request,
            f"Devolução de {quantity} unidade(s) de '{self.item.name}' ao estoque geral concluída com sucesso!",
        )
        return redirect("inventory:item-list")
