from django import forms

from core.forms import StyledModelForm
from organization.models import Branch, Department, Employee, EquipmentCategory, Supplier


class BranchForm(StyledModelForm):
    """Formulário para cadastro e edição de Filiais com validação de código único."""
    class Meta:
        model = Branch
        fields = ["name", "code", "city", "state"]


class DepartmentForm(StyledModelForm):
    """Formulário para cadastro e edição de Setores e vinculação das Filiais em que atua."""
    class Meta:
        model = Department
        fields = ["name", "branches"]
        help_texts = {
            "branches": "Adicione apenas as filiais que realmente pertencem a este setor.",
        }


class EmployeeForm(StyledModelForm):
    """Formulário para cadastro e edição de Colaboradores, permitindo e-mail opcional."""
    class Meta:
        model = Employee
        fields = ["full_name", "email", "job_title", "department", "branch", "is_active"]
        help_texts = {
            "email": "Campo opcional.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garante que o campo de e-mail seja opcional no formulário
        self.fields["email"].required = False

    def clean_email(self):
        """Trata e-mail vazio convertendo para None para não violar a restrição de unicidade."""
        email = self.cleaned_data.get("email")
        if not email or not str(email).strip():
            return None
        return str(email).strip()


class SupplierForm(StyledModelForm):
    """Formulário para cadastro e edição de Fornecedores parceiros."""
    class Meta:
        model = Supplier
        fields = ["legal_name", "cnpj", "contact_name", "email", "phone"]


class EquipmentCategoryForm(StyledModelForm):
    """Formulário para cadastro e edição de Categorias de Equipamentos de TI."""
    class Meta:
        model = EquipmentCategory
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

