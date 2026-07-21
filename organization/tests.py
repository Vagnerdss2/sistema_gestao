from django.test import TestCase

from organization.models import Branch, Department, Employee


class EmployeeModelTests(TestCase):
    def test_employee_branch_is_derived_from_department(self):
        branch = Branch.objects.create(name="Matriz", code="MTZ", city="Sao Paulo", state="SP")
        department = Department.objects.create(name="TI", branch=branch)

        employee = Employee.objects.create(
            full_name="Ana Souza",
            email="ana@example.com",
            job_title="Analista",
            department=department,
            branch=branch,
        )

        self.assertEqual(employee.branch, branch)
