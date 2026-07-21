from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from inventory.models import InventoryItem
from organization.models import Branch, Department, Employee, EquipmentCategory
from supportdesk.models import ServiceItemUsageType, ServiceOrder, ServiceOrderItemUsage
from supportdesk.services import process_service_item_usages


class ServiceOrderTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Matriz", code="MTZ", city="Sao Paulo", state="SP")
        self.department = Department.objects.create(name="TI", branch=self.branch)
        self.employee = Employee.objects.create(
            full_name="Paula Nunes",
            email="paula@example.com",
            job_title="Analista",
            department=self.department,
            branch=self.branch,
        )
        self.technician = Employee.objects.create(
            full_name="Leo Silva",
            email="leo@example.com",
            job_title="Tecnico",
            department=self.department,
            branch=self.branch,
        )
        self.category = EquipmentCategory.objects.create(name="Perifericos")
        self.item = InventoryItem.objects.create(
            name="Mouse USB",
            category=self.category,
            branch=self.branch,
            quantity=10,
            minimum_quantity=2,
        )

    def test_service_usage_consumes_stock(self):
        service_order = ServiceOrder.objects.create(
            title="Troca de mouse",
            short_description="Substituicao de periferico",
            solution_description="Mouse antigo com defeito foi substituido.",
            attended_user=self.employee,
            department=self.department,
            branch=self.branch,
            technician=self.technician,
            service_datetime=timezone.make_aware(datetime(2026, 7, 21, 10, 0)),
        )
        ServiceOrderItemUsage.objects.create(
            service_order=service_order,
            item=self.item,
            usage_type=ServiceItemUsageType.PART,
            quantity=2,
        )

        process_service_item_usages(service_order)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 8)
