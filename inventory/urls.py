from django.urls import path

from inventory import views

app_name = "inventory"

urlpatterns = [
    path("", views.InventoryItemListView.as_view(), name="item-list"),
    path("novo/", views.InventoryItemCreateView.as_view(), name="item-create"),
    path("<int:pk>/", views.InventoryItemDetailView.as_view(), name="item-detail"),
    path("<int:pk>/editar/", views.InventoryItemUpdateView.as_view(), name="item-update"),
    path("<int:pk>/adicionar-estoque/", views.InventoryItemAddStockView.as_view(), name="item-add-stock"),
    path("<int:pk>/vincular-colaborador/", views.InventoryItemAssignView.as_view(), name="item-assign"),
]
