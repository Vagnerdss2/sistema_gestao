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
