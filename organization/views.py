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


# ==============================================================================
# GESTÃO DE FILIAIS (BRANCHES)
# ==============================================================================

class BranchListView(AppListView):
    """Listagem de todas as filiais cadastradas na organização."""
    model = Branch
    page_title = "Filiais"
    page_description = "Cadastre e consulte as filiais atendidas pela operacao."
    create_url_name = "organization:branch-create"
    update_url_name = "organization:branch-update"


class BranchCreateView(AppCreateView):
    """Cadastro de nova filial (ex: código, nome, cidade e UF)."""
    model = Branch
    form_class = BranchForm
    page_title = "Nova Filial"
    page_description = "Registre uma nova filial."
    cancel_url_name = "organization:branch-list"
    success_url = reverse_lazy("organization:branch-list")


class BranchUpdateView(AppUpdateView):
    """Edição de informações de filial existente."""
    model = Branch
    form_class = BranchForm
    page_title = "Editar Filial"
    page_description = "Atualize os dados da filial."
    cancel_url_name = "organization:branch-list"
    success_url = reverse_lazy("organization:branch-list")


# ==============================================================================
# GESTÃO DE SETORES / DEPARTAMENTOS
# ==============================================================================

class DepartmentListView(AppListView):
    """Listagem de setores com pré-carregamento das filiais vinculadas (prefetch_related)."""
    model = Department
    queryset = Department.objects.prefetch_related("branches")
    template_name = "organization/department_list.html"
    page_title = "Setores"
    page_description = "Gerencie os setores vinculados a cada filial."
    create_url_name = "organization:department-create"
    update_url_name = "organization:department-update"


class DepartmentCreateView(AppCreateView):
    """Cadastro de novo setor e seleção de filiais em que opera."""
    model = Department
    form_class = DepartmentForm
    template_name = "organization/department_form.html"
    page_title = "Novo Setor"
    page_description = "Cadastre um setor para atendimento."
    cancel_url_name = "organization:department-list"
    success_url = reverse_lazy("organization:department-list")


class DepartmentUpdateView(AppUpdateView):
    """Edição de setor existente."""
    model = Department
    form_class = DepartmentForm
    template_name = "organization/department_form.html"
    page_title = "Editar Setor"
    page_description = "Atualize os dados do setor."
    cancel_url_name = "organization:department-list"
    success_url = reverse_lazy("organization:department-list")


# ==============================================================================
# GESTÃO DE COLABORADORES (EMPLOYEES)
# ==============================================================================

class EmployeeListView(AppListView):
    """Listagem de colaboradores com otimização select_related em setor e filial."""
    model = Employee
    queryset = Employee.objects.select_related("department", "branch")
    page_title = "Colaboradores"
    page_description = "Colaboradores usados como usuarios atendidos e responsaveis."
    create_url_name = "organization:employee-create"
    update_url_name = "organization:employee-update"


class EmployeeCreateView(AppCreateView):
    """Cadastro de novo colaborador."""
    model = Employee
    form_class = EmployeeForm
    page_title = "Novo Colaborador"
    page_description = "Cadastre um colaborador."
    cancel_url_name = "organization:employee-list"
    success_url = reverse_lazy("organization:employee-list")


class EmployeeUpdateView(AppUpdateView):
    """Edição de dados cadastrais de colaborador."""
    model = Employee
    form_class = EmployeeForm
    page_title = "Editar Colaborador"
    page_description = "Atualize os dados do colaborador."
    cancel_url_name = "organization:employee-list"
    success_url = reverse_lazy("organization:employee-list")


# ==============================================================================
# GESTÃO DE FORNECEDORES (SUPPLIERS)
# ==============================================================================

class SupplierListView(AppListView):
    """Listagem de fornecedores e prestadores cadastrados."""
    model = Supplier
    page_title = "Fornecedores"
    page_description = "Fornecedores habilitados para compras de TI."
    create_url_name = "organization:supplier-create"
    update_url_name = "organization:supplier-update"


class SupplierCreateView(AppCreateView):
    """Cadastro de novo fornecedor."""
    model = Supplier
    form_class = SupplierForm
    page_title = "Novo Fornecedor"
    page_description = "Cadastre um fornecedor."
    cancel_url_name = "organization:supplier-list"
    success_url = reverse_lazy("organization:supplier-list")


class SupplierUpdateView(AppUpdateView):
    """Edição de dados de fornecedor."""
    model = Supplier
    form_class = SupplierForm
    page_title = "Editar Fornecedor"
    page_description = "Atualize os dados do fornecedor."
    cancel_url_name = "organization:supplier-list"
    success_url = reverse_lazy("organization:supplier-list")


# ==============================================================================
# GESTÃO DE CATEGORIAS DE EQUIPAMENTOS
# ==============================================================================

class CategoryListView(AppListView):
    """Listagem de categorias de itens de TI."""
    model = EquipmentCategory
    page_title = "Categorias"
    page_description = "Categorias que organizam equipamentos, pecas e licencas."
    create_url_name = "organization:category-create"
    update_url_name = "organization:category-update"


class CategoryCreateView(AppCreateView):
    """Cadastro de nova categoria."""
    model = EquipmentCategory
    form_class = EquipmentCategoryForm
    page_title = "Nova Categoria"
    page_description = "Cadastre uma categoria de equipamento."
    cancel_url_name = "organization:category-list"
    success_url = reverse_lazy("organization:category-list")


class CategoryUpdateView(AppUpdateView):
    """Edição de categoria de equipamento."""
    model = EquipmentCategory
    form_class = EquipmentCategoryForm
    page_title = "Editar Categoria"
    page_description = "Atualize a categoria."
    cancel_url_name = "organization:category-list"
    success_url = reverse_lazy("organization:category-list")


# ==============================================================================
# API JSON AUXILIAR
# ==============================================================================

def employee_metadata(request, pk: int):
    """
    Endpoint JSON que retorna os dados de setor e filial de um colaborador selecionado.
    
    Utilizado por scripts JavaScript no frontend para autopreencher a filial e o setor
    ao selecionar um colaborador nas telas de Abertura de Ordem de Serviço ou Atribuição.
    """
    employee = Employee.objects.select_related("department", "branch").get(pk=pk)
    return JsonResponse(
        {
            "department_id": employee.department_id,
            "department_name": employee.department.name,
            "branch_id": employee.branch_id,
            "branch_name": employee.branch.name,
        }
    )

