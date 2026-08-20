from django.urls import path

from procurement import views

app_name = "procurement"

urlpatterns = [
    path("", views.PurchaseOrderListView.as_view(), name="purchase-list"),
    path("nova/", views.PurchaseOrderCreateView.as_view(), name="purchase-create"),
    path("<int:pk>/", views.PurchaseOrderDetailView.as_view(), name="purchase-detail"),
    path("<int:pk>/editar/", views.PurchaseOrderUpdateView.as_view(), name="purchase-update"),
]
