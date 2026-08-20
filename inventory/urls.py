"""
Rotas de URL do aplicativo Inventory (Estoque e Inventário).

Gerencia as rotas de:
- Aba Estoque Geral: /estoque/
- Aba Inventário de Colaboradores: /estoque/inventario/
- Entrada Rápida de Estoque (Reutilização de Item): /estoque/entrada-estoque/
- Atribuição Rápida a Colaborador: /estoque/atribuir-colaborador/
- Cadastro de Novo Item: /estoque/novo/
- Detalhamento de Item: /estoque/<pk>/
- Edição de Item: /estoque/<pk>/editar/
- Adição de Unidades: /estoque/<pk>/adicionar-estoque/
- Atribuição Específica: /estoque/<pk>/vincular-colaborador/
- Exclusão: /estoque/<pk>/excluir/
- Devolução ao Estoque: /estoque/<pk>/devolver-estoque/
- Descarte / Baixa Técnica: /estoque/<pk>/descartar/
"""

from django.urls import path

from inventory import views

app_name = "inventory"

urlpatterns = [
    # Aba Estoque Geral (apenas itens cadastrados e disponíveis no almoxarifado)
    path("", views.InventoryItemListView.as_view(), name="item-list"),

    # Aba Inventário (apenas itens que estão em uso por colaboradores)
    path("inventario/", views.CollaboratorInventoryListView.as_view(), name="inventory-list"),

    # Operações Globais de Movimentação
    path("entrada-estoque/", views.QuickStockEntryView.as_view(), name="quick-stock-entry"),
    path("atribuir-colaborador/", views.QuickAssignView.as_view(), name="quick-assign"),

    # CRUD de Itens
    path("novo/", views.InventoryItemCreateView.as_view(), name="item-create"),
    path("<int:pk>/", views.InventoryItemDetailView.as_view(), name="item-detail"),
    path("<int:pk>/editar/", views.InventoryItemUpdateView.as_view(), name="item-update"),
    path("<int:pk>/excluir/", views.InventoryItemDeleteView.as_view(), name="item-delete"),

    # Ações Específicas por Item
    path("<int:pk>/adicionar-estoque/", views.InventoryItemAddStockView.as_view(), name="item-add-stock"),
    path("<int:pk>/vincular-colaborador/", views.InventoryItemAssignView.as_view(), name="item-assign"),
    path("<int:pk>/devolver-estoque/", views.InventoryItemReturnStockView.as_view(), name="item-return-stock"),
    path("<int:pk>/descartar/", views.InventoryItemDiscardView.as_view(), name="item-discard"),
]


