"""
Rotas de URL do aplicativo Organization.

Gerencia os cadastros fundamentais de infraestrutura organizacional:
- Filiais (/organizacao/filiais/)
- Setores (/organizacao/setores/)
- Colaboradores (/organizacao/colaboradores/)
- Fornecedores (/organizacao/fornecedores/)
- Categorias de Equipamentos (/organizacao/categorias/)
- Metadata JSON de colaborador (/organizacao/colaboradores/<pk>/metadata/)
"""

from django.urls import path

from organization import views

app_name = "organization"

urlpatterns = [
    # Rotas de Filiais
    path("filiais/", views.BranchListView.as_view(), name="branch-list"),
    path("filiais/novo/", views.BranchCreateView.as_view(), name="branch-create"),
    path("filiais/<int:pk>/editar/", views.BranchUpdateView.as_view(), name="branch-update"),

    # Rotas de Setores
    path("setores/", views.DepartmentListView.as_view(), name="department-list"),
    path("setores/novo/", views.DepartmentCreateView.as_view(), name="department-create"),
    path("setores/<int:pk>/editar/", views.DepartmentUpdateView.as_view(), name="department-update"),

    # Rotas de Colaboradores
    path("colaboradores/", views.EmployeeListView.as_view(), name="employee-list"),
    path("colaboradores/novo/", views.EmployeeCreateView.as_view(), name="employee-create"),
    path("colaboradores/<int:pk>/editar/", views.EmployeeUpdateView.as_view(), name="employee-update"),
    path("colaboradores/<int:pk>/metadata/", views.employee_metadata, name="employee-metadata"),

    # Rotas de Fornecedores
    path("fornecedores/", views.SupplierListView.as_view(), name="supplier-list"),
    path("fornecedores/novo/", views.SupplierCreateView.as_view(), name="supplier-create"),
    path("fornecedores/<int:pk>/editar/", views.SupplierUpdateView.as_view(), name="supplier-update"),

    # Rotas de Categorias de Equipamento
    path("categorias/", views.CategoryListView.as_view(), name="category-list"),
    path("categorias/nova/", views.CategoryCreateView.as_view(), name="category-create"),
    path("categorias/<int:pk>/editar/", views.CategoryUpdateView.as_view(), name="category-update"),
]

