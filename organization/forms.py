from django import forms

from core.forms import StyledModelForm
from organization.models import Branch, Department, Employee, EquipmentCategory, Supplier


class BranchForm(StyledModelForm):
    class Meta:
        model = Branch
        fields = ["name", "code", "city", "state"]


class DepartmentForm(StyledModelForm):
    class Meta:
        model = Department
        fields = ["name", "branches"]
        widgets = {
            "branches": forms.SelectMultiple(attrs={"size": 6}),
        }


class EmployeeForm(StyledModelForm):
    class Meta:
        model = Employee
        fields = ["full_name", "email", "job_title", "department", "branch", "is_active"]


class SupplierForm(StyledModelForm):
    class Meta:
        model = Supplier
        fields = ["legal_name", "cnpj", "contact_name", "email", "phone"]


class EquipmentCategoryForm(StyledModelForm):
    class Meta:
        model = EquipmentCategory
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
