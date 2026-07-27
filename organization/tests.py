from django.test import TestCase

from organization.models import Branch, Department, Employee


class EmployeeModelTests(TestCase):
    def test_employee_branch_must_be_allowed_by_department(self):
        branch_sp = Branch.objects.create(name="Sao Paulo", code="SP", city="Sao Paulo", state="SP")
        branch_es = Branch.objects.create(name="Espirito Santo", code="ES", city="Vitoria", state="ES")
        department = Department.objects.create(name="Vendas")
        department.branches.set([branch_sp, branch_es])

        employee = Employee.objects.create(
            full_name="Ana Souza",
            email="ana@example.com",
            job_title="Analista",
            department=department,
            branch=branch_es,
        )

        self.assertEqual(employee.branch, branch_es)

    def test_employee_email_is_optional(self):
        branch = Branch.objects.create(name="Sao Paulo", code="SP", city="Sao Paulo", state="SP")
        department = Department.objects.create(name="TI")
        department.branches.set([branch])

        emp1 = Employee.objects.create(
            full_name="Carlos Silva",
            email="",
            job_title="Técnico",
            department=department,
            branch=branch,
        )
        emp2 = Employee.objects.create(
            full_name="Maria Santos",
            email=None,
            job_title="Analista",
            department=department,
            branch=branch,
        )

        self.assertIsNone(emp1.email)
        self.assertIsNone(emp2.email)
        self.assertEqual(Employee.objects.count(), 2)
