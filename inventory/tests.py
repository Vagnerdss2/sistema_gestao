from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from inventory.models import InventoryItem, InventoryStatus, MovementType, StockMovement
from organization.models import Branch, Department, Employee, EquipmentCategory

User = get_user_model()


class InventoryFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="password")
        self.client.force_login(self.user)

        self.branch = Branch.objects.create(name="Matriz SP", code="SP01", city="São Paulo", state="SP")
        self.department = Department.objects.create(name="TI")
        self.department.branches.add(self.branch)
        self.category = EquipmentCategory.objects.create(name="Periféricos", description="Periféricos em geral")

        self.employee1 = Employee.objects.create(
            full_name="João Silva",
            email="joao@example.com",
            job_title="Desenvolvedor",
            department=self.department,
            branch=self.branch,
        )
        self.employee2 = Employee.objects.create(
            full_name="Maria Santos",
            email="",  # Optional email
            job_title="Designer",
            department=self.department,
            branch=self.branch,
        )

        self.item = InventoryItem.objects.create(
            name="Mouse Ergonomico",
            category=self.category,
            brand="Logitech",
            model="MX Master 3",
            quantity=10,
            minimum_quantity=2,
            branch=self.branch,
        )

    def test_create_item_registers_initial_movement(self):
        url = reverse("inventory:item-create")
        data = {
            "name": "Teclado Mecanico",
            "category": self.category.pk,
            "brand": "Keychron",
            "model": "K2",
            "quantity": 5,
            "minimum_quantity": 1,
            "branch": self.branch.pk,
            "status": InventoryStatus.IN_STOCK,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        new_item = InventoryItem.objects.get(name="Teclado Mecanico")
        self.assertEqual(new_item.quantity, 5)
        self.assertEqual(new_item.movements.count(), 1)
        movement = new_item.movements.first()
        self.assertEqual(movement.movement_type, MovementType.ENTRY)
        self.assertEqual(movement.quantity, 5)

    def test_add_stock_units(self):
        url = reverse("inventory:item-add-stock", kwargs={"pk": self.item.pk})
        data = {
            "quantity": 15,
            "reference": "Lote #505",
            "notes": "Compra adicional",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 25)
        movement = self.item.movements.latest("created_at")
        self.assertEqual(movement.movement_type, MovementType.ENTRY)
        self.assertEqual(movement.quantity, 15)
        self.assertEqual(movement.reference, "Lote #505")

    def test_assign_employee_deducts_stock(self):
        url = reverse("inventory:item-assign", kwargs={"pk": self.item.pk})
        data = {
            "employee": self.employee1.pk,
            "quantity": 3,
            "notes": "Entrega para novo colaborador",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.item.refresh_from_db()
        # Initial quantity was 10, subtracted 3 -> quantity becomes 7
        self.assertEqual(self.item.quantity, 7)
        self.assertEqual(self.item.assigned_employee, self.employee1)

        movement = self.item.movements.latest("created_at")
        self.assertEqual(movement.movement_type, MovementType.EXIT)
        self.assertEqual(movement.quantity, 3)
        self.assertIn("João Silva", movement.reference)

    def test_assign_employee_excess_quantity_validation_error(self):
        url = reverse("inventory:item-assign", kwargs={"pk": self.item.pk})
        data = {
            "employee": self.employee1.pk,
            "quantity": 50,  # Only 10 available
            "notes": "Tentativa inválida",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "quantity", "Quantidade informada (50) é superior ao estoque disponível (10).")

    def test_search_inventory_by_user(self):
        # Assign item to employee1
        self.item.assigned_employee = self.employee1
        self.item.save()

        # Create unassigned item
        item2 = InventoryItem.objects.create(
            name="Monitor UltraWide",
            category=self.category,
            brand="LG",
            model="34WN80C",
            quantity=2,
            branch=self.branch,
        )

        url = reverse("inventory:item-list")

        # Search by employee name
        res1 = self.client.get(url, {"colaborador": self.employee1.pk})
        self.assertEqual(res1.status_code, 200)
        self.assertIn(self.item, res1.context["objects"])
        self.assertNotIn(item2, res1.context["objects"])

        # Search by general query matching employee name
        res2 = self.client.get(url, {"q": "João"})
        self.assertEqual(res2.status_code, 200)
        self.assertIn(self.item, res2.context["objects"])
        self.assertNotIn(item2, res2.context["objects"])

