from django.contrib import admin

from organization.models import Branch, Department, Employee, EquipmentCategory, Supplier


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "city", "state")
    search_fields = ("code", "name", "city", "state")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "branch")
    list_filter = ("branch",)
    search_fields = ("name",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "job_title", "department", "branch", "is_active")
    list_filter = ("branch", "department", "is_active")
    search_fields = ("full_name", "email", "job_title")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("legal_name", "cnpj", "contact_name", "email", "phone")
    search_fields = ("legal_name", "cnpj", "contact_name", "email")


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
