from django.urls import path

from supportdesk import views

app_name = "supportdesk"

urlpatterns = [
    path("", views.ServiceOrderListView.as_view(), name="service-list"),
    path("nova/", views.ServiceOrderCreateView.as_view(), name="service-create"),
    path("<int:pk>/", views.ServiceOrderDetailView.as_view(), name="service-detail"),
    path("<int:pk>/editar/", views.ServiceOrderUpdateView.as_view(), name="service-update"),
]
