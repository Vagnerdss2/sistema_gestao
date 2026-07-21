from django.urls import reverse_lazy

from core.views import AppCreateView, AppDetailView, AppListView, AppUpdateView
from inventory.forms import InventoryItemForm
from inventory.models import InventoryItem


class InventoryItemListView(AppListView):
    model = InventoryItem
    queryset = InventoryItem.objects.select_related("category", "branch", "assigned_employee")
    page_title = "Inventario e Estoque"
    page_description = "Controle de equipamentos, patrimonio e itens consumiveis."
    create_url_name = "inventory:item-create"
    update_url_name = "inventory:item-update"
    detail_url_name = "inventory:item-detail"


class InventoryItemCreateView(AppCreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    page_title = "Novo Item"
    page_description = "Cadastre um item de estoque ou patrimonio."
    cancel_url_name = "inventory:item-list"
    success_url = reverse_lazy("inventory:item-list")


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
