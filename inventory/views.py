from decimal import Decimal

from django.contrib import messages
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import FormView

from core.views import AppCreateView, AppDeleteView, AppDetailView, AppFormPageView, AppListView, AppUpdateView
from inventory.forms import (
    AddStockForm,
    AssignEmployeeForm,
    DiscardEquipmentForm,
    InventoryItemForm,
    QuickStockEntryForm,
    ReturnStockForm,
)
from inventory.models import InventoryItem, InventoryStatus, MovementType, StockMovement
from organization.models import Branch, Department, Employee, EquipmentCategory


# ==============================================================================
# ABA ESTOQUE (LISTA DE ITENS CADASTRADOS NO ESTOQUE GERAL)
# ==============================================================================

class InventoryItemListView(AppListView):
    """
    Aba Estoque: Exibe a listagem em formato de tabela de todos os produtos e equipamentos cadastrados.
    
    Regra:
    - Filtra estritamente itens onde 'assigned_employee__isnull=True' (apenas estoque geral disponível).
    - Apresenta métricas consolidadas (total de itens cadastrados, unidades físicas, valor total e alertas de estoque baixo).
    - Fornece filtros por texto (nome/marca/modelo/serial/patrimônio), filial, categoria, status e estoque baixo.
    """

    model = InventoryItem
    template_name = "inventory/item_list.html"
    page_title = "Controle de Estoque"
    page_description = "Itens e equipamentos cadastrados no estoque, quantidades disponíveis, data de aquisição e valores."
    create_url_name = "inventory:item-create"
    update_url_name = "inventory:item-update"
    detail_url_name = "inventory:item-detail"
    delete_url_name = "inventory:item-delete"

    def get_queryset(self):
        """Retorna apenas itens em estoque geral aplicando os filtros submetidos pelo usuário."""
        qs = (
            InventoryItem.objects.filter(assigned_employee__isnull=True)
            .select_related("category", "branch")
            .order_by("name", "brand", "model")
        )

        q = self.request.GET.get("q", "").strip()
        status_filter = self.request.GET.get("status", "").strip()
        branch_filter = self.request.GET.get("branch", "").strip()
        category_filter = self.request.GET.get("category", "").strip()
        low_stock_filter = self.request.GET.get("low_stock", "").strip()

        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(model__icontains=q)
                | Q(brand__icontains=q)
                | Q(serial_number__icontains=q)
                | Q(asset_tag__icontains=q)
                | Q(notes__icontains=q)
                | Q(category__name__icontains=q)
            )

        if status_filter:
            qs = qs.filter(status=status_filter)
        else:
            # Por padrão não exibe descartados a menos que seja explicitamente filtrado
            qs = qs.exclude(status=InventoryStatus.DISCARDED)

        if branch_filter and branch_filter.isdigit():
            qs = qs.filter(branch_id=int(branch_filter))

        if category_filter and category_filter.isdigit():
            qs = qs.filter(category_id=int(category_filter))

        if low_stock_filter == "1":
            qs = qs.filter(quantity__lte=F("minimum_quantity"))

        return qs

    def get_context_data(self, **kwargs):
        """Calcula os cards de métricas do topo da página e carrega opções de filtros."""
        context = super().get_context_data(**kwargs)
        stock_items = InventoryItem.objects.filter(assigned_employee__isnull=True).exclude(status=InventoryStatus.DISCARDED)

        total_registered_items = stock_items.count()
        total_physical_units = stock_items.aggregate(total=Sum("quantity"))["total"] or 0
        total_stock_value = stock_items.aggregate(
            total=Sum(F("quantity") * F("unit_price"), output_field=models.DecimalField())
        )["total"] or Decimal("0.00")
        low_stock_count = stock_items.filter(quantity__lte=F("minimum_quantity")).count()

        context["total_registered_items"] = total_registered_items
        context["total_physical_units"] = total_physical_units
        context["total_stock_value"] = total_stock_value
        context["low_stock_count"] = low_stock_count

        context["branches"] = Branch.objects.order_by("name")
        context["categories"] = EquipmentCategory.objects.order_by("name")
        context["status_choices"] = InventoryStatus.choices

        context["q"] = self.request.GET.get("q", "").strip()
        context["selected_status"] = self.request.GET.get("status", "").strip()
        context["selected_branch"] = self.request.GET.get("branch", "").strip()
        context["selected_category"] = self.request.GET.get("category", "").strip()
        context["selected_low_stock"] = self.request.GET.get("low_stock", "").strip()
        return context


# ==============================================================================
# ABA INVENTÁRIO (ITENS VINCULADOS A COLABORADORES)
# ==============================================================================

class CollaboratorInventoryListView(AppListView):
    """
    Aba Inventário: Lista exclusivamente os itens e equipamentos em uso nominal por colaboradores.
    
    Regra:
    - Filtra estritamente itens onde 'assigned_employee__isnull=False'.
    - Mostra colaborador responsável, filial, setor, valor do item, termo/observação e ações de devolução.
    """

    model = InventoryItem
    template_name = "inventory/inventory_list.html"
    page_title = "Inventário de Colaboradores"
    page_description = "Itens e equipamentos sob responsabilidade e em uso pelos colaboradores da empresa."
    create_url_name = ""
    update_url_name = "inventory:item-update"
    detail_url_name = "inventory:item-detail"
    delete_url_name = "inventory:item-delete"

    def get_queryset(self):
        """Retorna apenas itens com colaboradores vinculados aplicando os filtros."""
        qs = (
            InventoryItem.objects.filter(assigned_employee__isnull=False)
            .select_related("category", "branch", "assigned_employee", "assigned_employee__department", "assigned_employee__branch")
            .order_by("assigned_employee__full_name", "name")
        )

        q = self.request.GET.get("q", "").strip()
        employee_filter = self.request.GET.get("colaborador", "").strip()
        branch_filter = self.request.GET.get("branch", "").strip()
        department_filter = self.request.GET.get("department", "").strip()
        category_filter = self.request.GET.get("category", "").strip()

        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(model__icontains=q)
                | Q(brand__icontains=q)
                | Q(serial_number__icontains=q)
                | Q(asset_tag__icontains=q)
                | Q(notes__icontains=q)
                | Q(category__name__icontains=q)
                | Q(assigned_employee__full_name__icontains=q)
                | Q(assigned_employee__email__icontains=q)
            )

        if employee_filter:
            if employee_filter.isdigit():
                qs = qs.filter(assigned_employee_id=int(employee_filter))
            else:
                qs = qs.filter(
                    Q(assigned_employee__full_name__icontains=employee_filter)
                    | Q(assigned_employee__email__icontains=employee_filter)
                )

        if branch_filter and branch_filter.isdigit():
            qs = qs.filter(Q(branch_id=int(branch_filter)) | Q(assigned_employee__branch_id=int(branch_filter)))

        if department_filter and department_filter.isdigit():
            qs = qs.filter(assigned_employee__department_id=int(department_filter))

        if category_filter and category_filter.isdigit():
            qs = qs.filter(category_id=int(category_filter))

        return qs

    def get_context_data(self, **kwargs):
        """Calcula métricas dos equipamentos em uso e popula os dropdowns de filtro."""
        context = super().get_context_data(**kwargs)
        assigned_items = InventoryItem.objects.filter(assigned_employee__isnull=False)

        total_assigned_items = assigned_items.count()
        total_assigned_units = assigned_items.aggregate(total=Sum("quantity"))["total"] or 0
        total_assigned_value = assigned_items.aggregate(
            total=Sum(F("quantity") * F("unit_price"), output_field=models.DecimalField())
        )["total"] or Decimal("0.00")
        total_collaborators = assigned_items.values("assigned_employee_id").distinct().count()

        context["total_assigned_items"] = total_assigned_items
        context["total_assigned_units"] = total_assigned_units
        context["total_assigned_value"] = total_assigned_value
        context["total_collaborators"] = total_collaborators

        context["employees"] = Employee.objects.filter(is_active=True).order_by("full_name")
        context["branches"] = Branch.objects.order_by("name")
        context["departments"] = Department.objects.order_by("name")
        context["categories"] = EquipmentCategory.objects.order_by("name")

        context["q"] = self.request.GET.get("q", "").strip()
        context["selected_colaborador"] = self.request.GET.get("colaborador", "").strip()
        context["selected_branch"] = self.request.GET.get("branch", "").strip()
        context["selected_department"] = self.request.GET.get("department", "").strip()
        context["selected_category"] = self.request.GET.get("category", "").strip()
        return context


# ==============================================================================
# ENTRADA RÁPIDA DE ESTOQUE (REUTILIZAÇÃO DE CADASTRO)
# ==============================================================================

class QuickStockEntryView(AppFormPageView, FormView):
    """
    View de Entrada Rápida de Estoque (Reutilização de Cadastro).
    
    Permite ao usuário dar entrada de novas unidades selecionando um produto já existente
    no catálogo através de um select, evitando recadastrar marca, modelo e especificações toda vez.
    """

    form_class = QuickStockEntryForm
    template_name = "shared/object_form.html"
    cancel_url_name = "inventory:item-list"
    submit_label = "Registrar Entrada no Estoque"
    page_title = "Nova Entrada de Estoque"
    page_description = "Selecione um item já cadastrado para adicionar novas unidades ao estoque sem precisar recadastrar tudo."

    def form_valid(self, form):
        item = form.cleaned_data["item"]
        quantity = form.cleaned_data["quantity"]
        acquisition_date = form.cleaned_data.get("acquisition_date")
        unit_price = form.cleaned_data.get("unit_price")
        reference = form.cleaned_data.get("reference", "")
        notes = form.cleaned_data.get("notes", "")

        # Registra a movimentação atômica e atualiza o saldo do item
        StockMovement.register(
            item=item,
            movement_type=MovementType.ENTRY,
            quantity=quantity,
            unit_price=unit_price,
            acquisition_date=acquisition_date,
            reference=reference or "Entrada de estoque avulsa",
            notes=notes,
        )

        messages.success(
            self.request,
            f"Entrada de {quantity} unidade(s) registrada com sucesso para o item '{item.name}'! Estoque total: {item.quantity}.",
        )
        return redirect("inventory:item-list")


# ==============================================================================
# ATRIBUIÇÃO RÁPIDA A COLABORADOR (SAÍDA / VÍNCULO)
# ==============================================================================

class QuickAssignView(AppFormPageView, FormView):
    """
    View de Atribuição Direta de Equipamento ao Colaborador.
    
    Permite escolher um equipamento disponível em estoque e um colaborador,
    transferindo as unidades do saldo geral para o registro em uso no Inventário.
    """

    form_class = AssignEmployeeForm
    template_name = "shared/object_form.html"
    cancel_url_name = "inventory:inventory-list"
    submit_label = "Atribuir ao Colaborador"
    page_title = "Atribuir Equipamento ao Colaborador"
    page_description = "Selecione um item disponível em estoque e vincule-o ao colaborador responsável."

    def get_initial(self):
        """Pré-seleciona o item ou colaborador caso venham como parâmetros GET na URL."""
        initial = super().get_initial()
        item_id = self.request.GET.get("item")
        if item_id and item_id.isdigit():
            initial["item"] = int(item_id)
        employee_id = self.request.GET.get("employee")
        if employee_id and employee_id.isdigit():
            initial["employee"] = int(employee_id)
        return initial

    def form_valid(self, form):
        item = form.cleaned_data.get("item")
        employee = form.cleaned_data["employee"]
        quantity = form.cleaned_data["quantity"]
        notes = form.cleaned_data.get("notes", "")

        if not item:
            form.add_error("item", "Selecione um item do estoque para atribuir.")
            return self.form_invalid(form)

        with transaction.atomic():
            source_item = InventoryItem.objects.select_for_update().get(pk=item.pk)

            # Valida se há saldo suficiente no estoque para atender à entrega
            if source_item.quantity < quantity:
                form.add_error(
                    "quantity",
                    f"Quantidade informada ({quantity}) é superior ao estoque disponível ({source_item.quantity}).",
                )
                return self.form_invalid(form)

            # Caso 1: Item patrimonial único (com serial ou patrimônio)
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
                    unit_price=source_item.unit_price,
                    acquisition_date=source_item.acquisition_date,
                    reference=f"Vínculo com colaborador: {employee.full_name}",
                    notes=notes,
                )
            else:
                # Caso 2: Item em lote / genérico (periféricos, cabos, adaptadores)
                # Subtrai a quantidade do lote no estoque geral
                source_item.quantity -= quantity
                source_item.save(update_fields=["quantity", "updated_at"])

                # Registra a saída no estoque geral
                StockMovement.objects.create(
                    item=source_item,
                    movement_type=MovementType.EXIT,
                    quantity=quantity,
                    unit_price=source_item.unit_price,
                    acquisition_date=source_item.acquisition_date,
                    reference=f"Baixa por entrega ao colaborador: {employee.full_name}",
                    notes=notes,
                )

                # Localiza ou cria o registro alocado para o colaborador no status IN_USE
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
                    if source_item.unit_price and not assigned_item.unit_price:
                        assigned_item.unit_price = source_item.unit_price
                    if source_item.acquisition_date and not assigned_item.acquisition_date:
                        assigned_item.acquisition_date = source_item.acquisition_date
                    if notes:
                        assigned_item.notes = (assigned_item.notes + "\n" + notes).strip()
                    assigned_item.save(update_fields=["quantity", "unit_price", "acquisition_date", "notes", "updated_at"])
                else:
                    assigned_item = InventoryItem.objects.create(
                        name=source_item.name,
                        category=source_item.category,
                        brand=source_item.brand,
                        model=source_item.model,
                        serial_number="",
                        asset_tag="",
                        acquisition_date=source_item.acquisition_date,
                        unit_price=source_item.unit_price,
                        status=InventoryStatus.IN_USE,
                        quantity=quantity,
                        minimum_quantity=0,
                        branch=employee.branch,
                        assigned_employee=employee,
                        notes=notes or f"Vinculado ao colaborador em {timezone.localdate().strftime('%d/%m/%Y')}",
                    )

                # Registra o histórico de entrada no inventário do colaborador
                StockMovement.objects.create(
                    item=assigned_item,
                    movement_type=MovementType.ENTRY,
                    quantity=quantity,
                    unit_price=assigned_item.unit_price,
                    acquisition_date=assigned_item.acquisition_date,
                    reference=f"Item vinculado ao colaborador: {employee.full_name}",
                    notes=notes,
                )

        messages.success(
            self.request,
            f"Equipamento atribuído com sucesso! {quantity} unidade(s) de '{source_item.name}' vinculada(s) a {employee.full_name}.",
        )
        return redirect("inventory:inventory-list")


# ==============================================================================
# CRUD BÁSICO DE ITENS DE ESTOQUE
# ==============================================================================

class InventoryItemCreateView(AppCreateView):
    """Cadastro de um novo modelo/produto no catálogo de inventário."""
    model = InventoryItem
    form_class = InventoryItemForm
    page_title = "Cadastrar Novo Item no Catálogo"
    page_description = "Cadastre um novo item de estoque ou patrimônio. Este cadastro poderá ser reutilizado para futuras entradas de estoque."
    cancel_url_name = "inventory:item-list"
    success_url = reverse_lazy("inventory:item-list")

    def form_valid(self, form):
        """Ao criar o item com quantidade inicial > 0, gera automaticamente a primeira movimentação de entrada."""
        response = super().form_valid(form)
        if self.object.quantity > 0:
            StockMovement.objects.create(
                item=self.object,
                movement_type=MovementType.ENTRY,
                quantity=self.object.quantity,
                unit_price=self.object.unit_price,
                acquisition_date=self.object.acquisition_date,
                reference="Entrada inicial de cadastro",
                notes="Estoque registrado na criação do item.",
            )
        messages.success(self.request, f"Item '{self.object.name}' cadastrado com sucesso!")
        return response


class InventoryItemUpdateView(AppUpdateView):
    """Edição de dados cadastrais de um item existente."""
    model = InventoryItem
    form_class = InventoryItemForm
    page_title = "Editar Item"
    page_description = "Atualize dados cadastrais, data de aquisição, valor, estoque e filiais."
    cancel_url_name = "inventory:item-list"
    success_url = reverse_lazy("inventory:item-list")


class InventoryItemDeleteView(AppDeleteView):
    """Confirmação e exclusão definitiva de um item de estoque."""
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
    """Exibição detalhada de um item, especificações, valores, status e histórico de movimentações."""
    model = InventoryItem
    queryset = InventoryItem.objects.select_related("category", "branch", "assigned_employee").prefetch_related("movements")
    page_title = "Detalhes do Item"
    list_url_name = "inventory:item-list"
    template_name = "inventory/item_detail.html"


# ==============================================================================
# OPERAÇÕES ESPECÍFICAS DE ESTOQUE (ADICIONAR, DEVOLVER, DESCARTAR)
# ==============================================================================

class InventoryItemAddStockView(AppFormPageView, FormView):
    """Adiciona unidades de estoque diretamente a um item específico selecionado na tabela."""
    form_class = AddStockForm
    template_name = "shared/object_form.html"
    cancel_url_name = "inventory:item-list"
    submit_label = "Adicionar Unidades ao Estoque"

    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(InventoryItem, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Adicionar Unidades ao Estoque: {self.item.name}"
        context["page_description"] = f"Estoque atual: {self.item.quantity} unidade(s) | Filial: {self.item.branch.name}"
        return context

    def form_valid(self, form):
        quantity = form.cleaned_data["quantity"]
        acquisition_date = form.cleaned_data.get("acquisition_date")
        unit_price = form.cleaned_data.get("unit_price")
        reference = form.cleaned_data.get("reference", "")
        notes = form.cleaned_data.get("notes", "")

        StockMovement.register(
            item=self.item,
            movement_type=MovementType.ENTRY,
            quantity=quantity,
            unit_price=unit_price,
            acquisition_date=acquisition_date,
            reference=reference or "Entrada manual de unidades",
            notes=notes,
        )
        messages.success(
            self.request,
            f"Adicionadas {quantity} unidade(s) ao item '{self.item.name}'. Novo total em estoque: {self.item.quantity}.",
        )
        return redirect("inventory:item-list")


class InventoryItemAssignView(AppFormPageView, FormView):
    """Vincula uma unidade deste item específico a um colaborador, dando baixa no saldo geral."""
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

            # Item com serial/patrimônio
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
                    unit_price=source_item.unit_price,
                    acquisition_date=source_item.acquisition_date,
                    reference=f"Vínculo com colaborador: {employee.full_name}",
                    notes=notes,
                )
            else:
                # Item em lote
                source_item.quantity -= quantity
                source_item.save(update_fields=["quantity", "updated_at"])

                StockMovement.objects.create(
                    item=source_item,
                    movement_type=MovementType.EXIT,
                    quantity=quantity,
                    unit_price=source_item.unit_price,
                    acquisition_date=source_item.acquisition_date,
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
                    if source_item.unit_price and not assigned_item.unit_price:
                        assigned_item.unit_price = source_item.unit_price
                    if source_item.acquisition_date and not assigned_item.acquisition_date:
                        assigned_item.acquisition_date = source_item.acquisition_date
                    if notes:
                        assigned_item.notes = (assigned_item.notes + "\n" + notes).strip()
                    assigned_item.save(update_fields=["quantity", "unit_price", "acquisition_date", "notes", "updated_at"])
                else:
                    assigned_item = InventoryItem.objects.create(
                        name=source_item.name,
                        category=source_item.category,
                        brand=source_item.brand,
                        model=source_item.model,
                        serial_number="",
                        asset_tag="",
                        acquisition_date=source_item.acquisition_date,
                        unit_price=source_item.unit_price,
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
                    unit_price=assigned_item.unit_price,
                    acquisition_date=assigned_item.acquisition_date,
                    reference=f"Item vinculado ao colaborador: {employee.full_name}",
                    notes=notes,
                )

        messages.success(
            self.request,
            f"Baixa de {quantity} unidade(s) efetuada com sucesso! O item agora consta na aba Inventário vinculado a {employee.full_name}.",
        )
        return redirect("inventory:inventory-list")


class InventoryItemReturnStockView(AppFormPageView, FormView):
    """Devolve unidades de um item que estava com colaborador de volta ao estoque geral."""
    form_class = ReturnStockForm
    template_name = "shared/object_form.html"
    cancel_url_name = "inventory:inventory-list"
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

            # Item individual serializado
            if (assigned_item.serial_number or assigned_item.asset_tag) and assigned_item.quantity == 1:
                assigned_item.assigned_employee = None
                assigned_item.status = InventoryStatus.IN_STOCK
                assigned_item.save(update_fields=["assigned_employee", "status", "updated_at"])

                StockMovement.objects.create(
                    item=assigned_item,
                    movement_type=MovementType.ENTRY,
                    quantity=1,
                    unit_price=assigned_item.unit_price,
                    acquisition_date=assigned_item.acquisition_date,
                    reference=f"Devolução do colaborador: {emp_name}",
                    notes=notes,
                )
            else:
                # Item em lote: diminui a posse do colaborador e retorna ao pool geral
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
                        "unit_price": assigned_item.unit_price,
                        "acquisition_date": assigned_item.acquisition_date,
                        "notes": "Estoque geral unificado",
                    },
                )
                pool_item.quantity += quantity
                if not pool_item.unit_price and assigned_item.unit_price:
                    pool_item.unit_price = assigned_item.unit_price
                if not pool_item.acquisition_date and assigned_item.acquisition_date:
                    pool_item.acquisition_date = assigned_item.acquisition_date
                pool_item.save(update_fields=["quantity", "unit_price", "acquisition_date", "updated_at"])

                StockMovement.objects.create(
                    item=pool_item,
                    movement_type=MovementType.ENTRY,
                    quantity=quantity,
                    unit_price=pool_item.unit_price,
                    acquisition_date=pool_item.acquisition_date,
                    reference=f"Devolução de estoque do colaborador: {emp_name}",
                    notes=notes,
                )

        messages.success(
            self.request,
            f"Devolução de {quantity} unidade(s) de '{self.item.name}' ao estoque geral concluída com sucesso!",
        )
        return redirect("inventory:inventory-list")


class InventoryItemDiscardView(AppFormPageView, FormView):
    """Registra a baixa / descarte definitivo de um equipamento por defeito, queima ou obsolescência."""
    form_class = DiscardEquipmentForm
    template_name = "shared/object_form.html"
    cancel_url_name = "inventory:item-list"
    submit_label = "Confirmar Descarte"

    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(InventoryItem, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Descartar Equipamento: {self.item.name}"
        context["page_description"] = f"Patrimônio/Série: {self.item.asset_tag or self.item.serial_number or 'S/N'} | Filial: {self.item.branch.name}"
        return context

    def form_valid(self, form):
        reason = form.cleaned_data["reason"]

        with transaction.atomic():
            item = InventoryItem.objects.select_for_update().get(pk=self.item.pk)
            item.status = InventoryStatus.DISCARDED
            item.assigned_employee = None
            if item.notes:
                item.notes = (item.notes + f"\n[Descartado em {timezone.localdate().strftime('%d/%m/%Y')}]: {reason}").strip()
            else:
                item.notes = f"[Descartado em {timezone.localdate().strftime('%d/%m/%Y')}]: {reason}"
            item.save(update_fields=["status", "assigned_employee", "notes", "updated_at"])

            StockMovement.objects.create(
                item=item,
                movement_type=MovementType.EXIT,
                quantity=item.quantity or 1,
                unit_price=item.unit_price,
                acquisition_date=item.acquisition_date,
                reference="Baixa por Descarte",
                notes=reason,
            )

        messages.success(
            self.request,
            f"O equipamento '{item.name}' foi marcado como Descartado com sucesso.",
        )
        return redirect("inventory:item-list")



