from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.templatetags.core_extras import currency, multiply
from inventory.models import InventoryItem, InventoryStatus
from organization.models import Branch, Department, Employee, EquipmentCategory

User = get_user_model()


class CoreNavigationAndDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="password")
        self.client.force_login(self.user)

        self.branch = Branch.objects.create(name="Matriz SP", code="SP01", city="São Paulo", state="SP")
        self.department = Department.objects.create(name="TI")
        self.department.branches.add(self.branch)
        self.category = EquipmentCategory.objects.create(name="Periféricos")

        self.employee = Employee.objects.create(
            full_name="Carlos Lima",
            job_title="Analista",
            department=self.department,
            branch=self.branch,
        )

        self.stock_item = InventoryItem.objects.create(
            name="Notebook Dell",
            category=self.category,
            brand="Dell",
            model="Latitude 3420",
            quantity=5,
            unit_price=Decimal("3500.00"),
            branch=self.branch,
            status=InventoryStatus.IN_STOCK,
        )

        self.assigned_item = InventoryItem.objects.create(
            name="Notebook Dell",
            category=self.category,
            brand="Dell",
            model="Latitude 3420",
            quantity=1,
            unit_price=Decimal("3500.00"),
            branch=self.branch,
            assigned_employee=self.employee,
            status=InventoryStatus.IN_USE,
        )

    def test_navigation_items_contain_estoque_and_inventario_and_no_compras(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        nav_labels = [item["label"] for item in response.context["navigation_items"]]
        self.assertIn("Estoque", nav_labels)
        self.assertIn("Inventário", nav_labels)
        self.assertNotIn("Compras", nav_labels)

    def test_dashboard_metrics(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        inventory_totals = response.context["inventory_totals"]
        self.assertEqual(inventory_totals["total_in_stock"], 5)
        self.assertEqual(inventory_totals["total_in_use"], 1)
        self.assertEqual(inventory_totals["stock_value"], Decimal("17500.00"))

    def test_currency_and_multiply_filters(self):
        self.assertEqual(currency(Decimal("1500.50")), "R$ 1.500,50")
        self.assertEqual(currency(0), "R$ 0,00")
        self.assertEqual(currency(None), "R$ 0,00")
        self.assertEqual(multiply(5, 10), Decimal("50.00"))

