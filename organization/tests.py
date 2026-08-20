from django.core.exceptions import ValidationError
from django.test import TestCase

from organization.models import Branch, Department, Employee


class EmployeeModelTests(TestCase):
    def setUp(self):
        self.branch_sp = Branch.objects.create(name="Sao Paulo", code="SP", city="Sao Paulo", state="SP")
        self.branch_es = Branch.objects.create(name="Espirito Santo", code="ES", city="Vitoria", state="ES")
        self.department = Department.objects.create(name="TI")
        self.department.branches.set([self.branch_sp, self.branch_es])

    def test_employee_branch_must_be_allowed_by_department(self):
        department_vendas = Department.objects.create(name="Vendas")
        department_vendas.branches.set([self.branch_sp, self.branch_es])

        employee = Employee.objects.create(
            full_name="Ana Souza",
            email="ana@example.com",
            job_title="Analista",
            department=department_vendas,
            branch=self.branch_es,
        )

        self.assertEqual(employee.branch, self.branch_es)

    def test_employee_email_is_optional(self):
        emp1 = Employee.objects.create(
            full_name="Carlos Silva",
            email="",
            job_title="Técnico",
            department=self.department,
            branch=self.branch_sp,
        )
        emp2 = Employee.objects.create(
            full_name="Maria Santos",
            email=None,
            job_title="Analista",
            department=self.department,
            branch=self.branch_sp,
        )

        self.assertIsNone(emp1.email)
        self.assertIsNone(emp2.email)
        self.assertEqual(Employee.objects.count(), 2)

    def test_employee_code_auto_generated_sequentially_starting_from_one(self):
        """Testa se os códigos são gerados sequencialmente a partir do número 1."""
        emp1 = Employee.objects.create(
            full_name="Primeiro Colaborador",
            job_title="Dev",
            department=self.department,
            branch=self.branch_sp,
        )
        emp2 = Employee.objects.create(
            full_name="Segundo Colaborador",
            job_title="Dev",
            department=self.department,
            branch=self.branch_sp,
        )
        emp3 = Employee.objects.create(
            full_name="Terceiro Colaborador",
            job_title="Dev",
            department=self.department,
            branch=self.branch_sp,
        )

        self.assertEqual(emp1.code, 1)
        self.assertEqual(emp2.code, 2)
        self.assertEqual(emp3.code, 3)

    def test_prevents_duplicate_employee_creation(self):
        """Testa se a validação impede a criação de colaboradores duplicados no mesmo setor/filial."""
        Employee.objects.create(
            full_name="Lucas Fernandes",
            job_title="Suporte",
            department=self.department,
            branch=self.branch_sp,
        )

        duplicate_emp = Employee(
            full_name="Lucas Fernandes",
            job_title="Suporte TI",
            department=self.department,
            branch=self.branch_sp,
        )

        with self.assertRaises(ValidationError) as ctx:
            duplicate_emp.full_clean()

        self.assertIn("full_name", ctx.exception.message_dict)
        self.assertTrue(any("Já existe um colaborador" in err for err in ctx.exception.message_dict["full_name"]))

    def test_create_employee_via_view_without_email(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        User = get_user_model()
        user = User.objects.create_user(username="admin", password="password")
        self.client.force_login(user)

        url = reverse("organization:employee-create")
        data = {
            "full_name": "João Sem Email",
            "email": "",
            "job_title": "Assistente",
            "department": self.department.pk,
            "branch": self.branch_sp.pk,
            "is_active": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Employee.objects.filter(full_name="João Sem Email").exists())
        emp = Employee.objects.get(full_name="João Sem Email")
        self.assertIsNone(emp.email)
        self.assertIsNotNone(emp.code)
        self.assertEqual(emp.code, 1)

