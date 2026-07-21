from django.urls import path

from inventory import views

app_name = "inventory"

urlpatterns = [
    path("", views.InventoryItemListView.as_view(), name="item-list"),
    path("novo/", views.InventoryItemCreateView.as_view(), name="item-create"),
    path("<int:pk>/", views.InventoryItemDetailView.as_view(), name="item-detail"),
    path("<int:pk>/editar/", views.InventoryItemUpdateView.as_view(), name="item-update"),
]
