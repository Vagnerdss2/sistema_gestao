from datetime import date
from decimal import Decimal

from django.test import TestCase

from inventory.models import InventoryItem
from organization.models import Branch, Employee, EquipmentCategory, Supplier, Department
from procurement.models import PurchaseOrder, PurchaseOrderItem, PurchaseStatus
from procurement.services import refresh_purchase_totals, sync_purchase_order_to_inventory


class ProcurementServiceTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Matriz", code="MTZ", city="Sao Paulo", state="SP")
        self.department = Department.objects.create(name="TI")
        self.department.branches.set([self.branch])
        self.employee = Employee.objects.create(
            full_name="Carlos Lima",
            email="carlos@example.com",
            job_title="Coordenador",
            department=self.department,
            branch=self.branch,
        )
        self.category = EquipmentCategory.objects.create(name="Notebooks")
        self.supplier = Supplier.objects.create(legal_name="Fornecedor XPTO", cnpj="12.345.678/0001-99")

    def test_delivered_purchase_creates_inventory_and_updates_totals(self):
        purchase = PurchaseOrder.objects.create(
            title="Compra de notebooks",
            branch=self.branch,
            supplier=self.supplier,
            requester=self.employee,
            purchase_date=date.today(),
            status=PurchaseStatus.DELIVERED,
        )
        PurchaseOrderItem.objects.create(
            purchase_order=purchase,
            item_name="Notebook Dell",
            category=self.category,
            quantity=2,
            estimated_unit_price=Decimal("4500.00"),
            actual_unit_price=Decimal("4300.00"),
        )

        refresh_purchase_totals(purchase)
        sync_purchase_order_to_inventory(purchase)

        purchase.refresh_from_db()
        inventory_item = InventoryItem.objects.get(name="Notebook Dell")

        self.assertTrue(purchase.inventory_processed)
        self.assertEqual(purchase.estimated_total, Decimal("9000.00"))
        self.assertEqual(purchase.actual_total, Decimal("8600.00"))
        self.assertEqual(inventory_item.quantity, 2)


class ProcurementFormAndViewsTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.force_login(self.user)
        self.branch = Branch.objects.create(name="Matriz", code="MTZ", city="Sao Paulo", state="SP")
        self.supplier = Supplier.objects.create(legal_name="Fornecedor XPTO", cnpj="12.345.678/0001-99")

    def test_purchase_form_formats_date_for_html5_input(self):
        from procurement.forms import PurchaseOrderForm

        purchase = PurchaseOrder.objects.create(
            title="Compra de teste",
            branch=self.branch,
            supplier=self.supplier,
            purchase_date=date(2026, 7, 15),
            estimated_total=Decimal("1500.00"),
            actual_total=Decimal("1400.00"),
        )
        form = PurchaseOrderForm(instance=purchase)
        rendered_field = str(form["purchase_date"])
        self.assertIn('value="2026-07-15"', rendered_field)

    def test_purchase_totals_persisted_from_form_when_no_items(self):
        purchase = PurchaseOrder.objects.create(
            title="Compra sem itens",
            branch=self.branch,
            supplier=self.supplier,
            purchase_date=date(2026, 7, 15),
            estimated_total=Decimal("2500.00"),
            actual_total=Decimal("2300.00"),
        )
        refresh_purchase_totals(purchase)
        purchase.refresh_from_db()
        self.assertEqual(purchase.estimated_total, Decimal("2500.00"))
        self.assertEqual(purchase.actual_total, Decimal("2300.00"))

    def test_create_and_edit_purchase_via_view(self):
        from django.urls import reverse

        # Create
        category = EquipmentCategory.objects.create(name="Servidores")
        post_data = {
            "title": "Nova Compra Servidor",
            "branch": self.branch.pk,
            "supplier": self.supplier.pk,
            "purchase_date": "2026-07-20",
            "estimated_total": "12000.00",
            "actual_total": "11500.00",
            "status": "pending",
            "items-TOTAL_FORMS": "0",
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(reverse("procurement:purchase-create"), post_data)
        self.assertEqual(response.status_code, 302)

        purchase = PurchaseOrder.objects.get(title="Nova Compra Servidor")
        self.assertEqual(purchase.estimated_total, Decimal("12000.00"))
        self.assertEqual(purchase.actual_total, Decimal("11500.00"))
        self.assertEqual(purchase.purchase_date, date(2026, 7, 20))

        # Get Edit page to verify date rendered in form
        edit_url = reverse("procurement:purchase-update", kwargs={"pk": purchase.pk})
        get_response = self.client.get(edit_url)
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, 'value="2026-07-20"')

        # Edit POST
        post_data["title"] = "Nova Compra Servidor Editado"
        post_data["estimated_total"] = "13000.00"
        post_data["actual_total"] = "12500.00"
        post_data["items-INITIAL_FORMS"] = "0"
        post_data["items-TOTAL_FORMS"] = "0"
        post_response = self.client.post(edit_url, post_data)
        self.assertEqual(post_response.status_code, 302)

        purchase.refresh_from_db()
        self.assertEqual(purchase.title, "Nova Compra Servidor Editado")
        self.assertEqual(purchase.estimated_total, Decimal("13000.00"))
        self.assertEqual(purchase.actual_total, Decimal("12500.00"))
        self.assertEqual(purchase.purchase_date, date(2026, 7, 20))


