"""
Rotas de URL do aplicativo Support Desk (Ordens de Serviço e Atendimentos).

- /servicos/ : Listagem de atendimentos executados
- /servicos/nova/ : Abertura de nova Ordem de Serviço
- /servicos/<pk>/ : Detalhes do atendimento e peças
- /servicos/<pk>/editar/ : Edição de atendimento existente
"""

from django.urls import path

from supportdesk import views

app_name = "supportdesk"

urlpatterns = [
    path("", views.ServiceOrderListView.as_view(), name="service-list"),
    path("nova/", views.ServiceOrderCreateView.as_view(), name="service-create"),
    path("<int:pk>/", views.ServiceOrderDetailView.as_view(), name="service-detail"),
    path("<int:pk>/editar/", views.ServiceOrderUpdateView.as_view(), name="service-update"),
]

