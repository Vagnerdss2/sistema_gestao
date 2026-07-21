from django.urls import path

from organization import views

app_name = "organization"

urlpatterns = [
    path("filiais/", views.BranchListView.as_view(), name="branch-list"),
    path("filiais/novo/", views.BranchCreateView.as_view(), name="branch-create"),
    path("filiais/<int:pk>/editar/", views.BranchUpdateView.as_view(), name="branch-update"),
    path("setores/", views.DepartmentListView.as_view(), name="department-list"),
    path("setores/novo/", views.DepartmentCreateView.as_view(), name="department-create"),
    path("setores/<int:pk>/editar/", views.DepartmentUpdateView.as_view(), name="department-update"),
    path("colaboradores/", views.EmployeeListView.as_view(), name="employee-list"),
    path("colaboradores/novo/", views.EmployeeCreateView.as_view(), name="employee-create"),
    path("colaboradores/<int:pk>/editar/", views.EmployeeUpdateView.as_view(), name="employee-update"),
    path("fornecedores/", views.SupplierListView.as_view(), name="supplier-list"),
    path("fornecedores/novo/", views.SupplierCreateView.as_view(), name="supplier-create"),
    path("fornecedores/<int:pk>/editar/", views.SupplierUpdateView.as_view(), name="supplier-update"),
    path("categorias/", views.CategoryListView.as_view(), name="category-list"),
    path("categorias/nova/", views.CategoryCreateView.as_view(), name="category-create"),
    path("categorias/<int:pk>/editar/", views.CategoryUpdateView.as_view(), name="category-update"),
    path("colaboradores/<int:pk>/metadata/", views.employee_metadata, name="employee-metadata"),
]
