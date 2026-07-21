from django.http import JsonResponse
from django.urls import reverse_lazy

from core.views import AppCreateView, AppListView, AppUpdateView
from organization.forms import (
    BranchForm,
    DepartmentForm,
    EmployeeForm,
    EquipmentCategoryForm,
    SupplierForm,
)
from organization.models import Branch, Department, Employee, EquipmentCategory, Supplier


class BranchListView(AppListView):
    model = Branch
    page_title = "Filiais"
    page_description = "Cadastre e consulte as filiais atendidas pela operacao."
    create_url_name = "organization:branch-create"
    update_url_name = "organization:branch-update"


class BranchCreateView(AppCreateView):
    model = Branch
    form_class = BranchForm
    page_title = "Nova Filial"
    page_description = "Registre uma nova filial."
    cancel_url_name = "organization:branch-list"
    success_url = reverse_lazy("organization:branch-list")


class BranchUpdateView(AppUpdateView):
    model = Branch
    form_class = BranchForm
    page_title = "Editar Filial"
    page_description = "Atualize os dados da filial."
    cancel_url_name = "organization:branch-list"
    success_url = reverse_lazy("organization:branch-list")


class DepartmentListView(AppListView):
    model = Department
    queryset = Department.objects.select_related("branch")
    page_title = "Setores"
    page_description = "Gerencie os setores vinculados a cada filial."
    create_url_name = "organization:department-create"
    update_url_name = "organization:department-update"


class DepartmentCreateView(AppCreateView):
    model = Department
    form_class = DepartmentForm
    page_title = "Novo Setor"
    page_description = "Cadastre um setor para atendimento."
    cancel_url_name = "organization:department-list"
    success_url = reverse_lazy("organization:department-list")


class DepartmentUpdateView(AppUpdateView):
    model = Department
    form_class = DepartmentForm
    page_title = "Editar Setor"
    page_description = "Atualize os dados do setor."
    cancel_url_name = "organization:department-list"
    success_url = reverse_lazy("organization:department-list")


class EmployeeListView(AppListView):
    model = Employee
    queryset = Employee.objects.select_related("department", "branch")
    page_title = "Colaboradores"
    page_description = "Colaboradores usados como usuarios atendidos e responsaveis."
    create_url_name = "organization:employee-create"
    update_url_name = "organization:employee-update"


class EmployeeCreateView(AppCreateView):
    model = Employee
    form_class = EmployeeForm
    page_title = "Novo Colaborador"
    page_description = "Cadastre um colaborador."
    cancel_url_name = "organization:employee-list"
    success_url = reverse_lazy("organization:employee-list")


class EmployeeUpdateView(AppUpdateView):
    model = Employee
    form_class = EmployeeForm
    page_title = "Editar Colaborador"
    page_description = "Atualize os dados do colaborador."
    cancel_url_name = "organization:employee-list"
    success_url = reverse_lazy("organization:employee-list")


class SupplierListView(AppListView):
    model = Supplier
    page_title = "Fornecedores"
    page_description = "Fornecedores habilitados para compras de TI."
    create_url_name = "organization:supplier-create"
    update_url_name = "organization:supplier-update"


class SupplierCreateView(AppCreateView):
    model = Supplier
    form_class = SupplierForm
    page_title = "Novo Fornecedor"
    page_description = "Cadastre um fornecedor."
    cancel_url_name = "organization:supplier-list"
    success_url = reverse_lazy("organization:supplier-list")


class SupplierUpdateView(AppUpdateView):
    model = Supplier
    form_class = SupplierForm
    page_title = "Editar Fornecedor"
    page_description = "Atualize os dados do fornecedor."
    cancel_url_name = "organization:supplier-list"
    success_url = reverse_lazy("organization:supplier-list")


class CategoryListView(AppListView):
    model = EquipmentCategory
    page_title = "Categorias"
    page_description = "Categorias que organizam equipamentos, pecas e licencas."
    create_url_name = "organization:category-create"
    update_url_name = "organization:category-update"


class CategoryCreateView(AppCreateView):
    model = EquipmentCategory
    form_class = EquipmentCategoryForm
    page_title = "Nova Categoria"
    page_description = "Cadastre uma categoria de equipamento."
    cancel_url_name = "organization:category-list"
    success_url = reverse_lazy("organization:category-list")


class CategoryUpdateView(AppUpdateView):
    model = EquipmentCategory
    form_class = EquipmentCategoryForm
    page_title = "Editar Categoria"
    page_description = "Atualize a categoria."
    cancel_url_name = "organization:category-list"
    success_url = reverse_lazy("organization:category-list")


def employee_metadata(request, pk: int):
    """Retorna setor e filial do colaborador para preenchimento dinamico."""

    employee = Employee.objects.select_related("department", "branch").get(pk=pk)
    return JsonResponse(
        {
            "department_id": employee.department_id,
            "department_name": employee.department.name,
            "branch_id": employee.branch_id,
            "branch_name": employee.branch.name,
        }
    )
