from datetime import date
from decimal import Decimal

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
            acquisition_date=date(2026, 1, 15),
            unit_price=Decimal("450.00"),
            quantity=10,
            minimum_quantity=2,
            branch=self.branch,
        )

    def test_create_item_with_acquisition_date_and_unit_price(self):
        url = reverse("inventory:item-create")
        data = {
            "name": "Teclado Mecanico",
            "category": self.category.pk,
            "brand": "Keychron",
            "model": "K2",
            "acquisition_date": "2026-03-10",
            "unit_price": "650.00",
            "quantity": 5,
            "minimum_quantity": 1,
            "branch": self.branch.pk,
            "status": InventoryStatus.IN_STOCK,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        new_item = InventoryItem.objects.get(name="Teclado Mecanico")
        self.assertEqual(new_item.quantity, 5)
        self.assertEqual(new_item.acquisition_date, date(2026, 3, 10))
        self.assertEqual(new_item.unit_price, Decimal("650.00"))
        self.assertEqual(new_item.total_value, Decimal("3250.00"))
        self.assertEqual(new_item.movements.count(), 1)
        movement = new_item.movements.first()
        self.assertEqual(movement.movement_type, MovementType.ENTRY)
        self.assertEqual(movement.quantity, 5)
        self.assertEqual(movement.unit_price, Decimal("650.00"))

    def test_quick_stock_entry_reusing_registered_item(self):
        """Testa entrada de estoque selecionando um item já cadastrado (reuso do cadastro)."""
        url = reverse("inventory:quick-stock-entry")
        data = {
            "item": self.item.pk,
            "quantity": 8,
            "acquisition_date": "2026-08-20",
            "unit_price": "480.00",
            "reference": "NF 98765 - Novo Lote",
            "notes": "Reabastecimento sem recadastrar item",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 18)
        self.assertEqual(self.item.unit_price, Decimal("480.00"))
        self.assertEqual(self.item.acquisition_date, date(2026, 8, 20))

        movement = self.item.movements.latest("created_at")
        self.assertEqual(movement.movement_type, MovementType.ENTRY)
        self.assertEqual(movement.quantity, 8)
        self.assertEqual(movement.unit_price, Decimal("480.00"))
        self.assertEqual(movement.reference, "NF 98765 - Novo Lote")

    def test_add_stock_units_via_item_action(self):
        url = reverse("inventory:item-add-stock", kwargs={"pk": self.item.pk})
        data = {
            "quantity": 15,
            "acquisition_date": "2026-05-01",
            "unit_price": "460.00",
            "reference": "Lote #505",
            "notes": "Compra adicional",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 25)
        self.assertEqual(self.item.unit_price, Decimal("460.00"))
        movement = self.item.movements.latest("created_at")
        self.assertEqual(movement.movement_type, MovementType.ENTRY)
        self.assertEqual(movement.quantity, 15)
        self.assertEqual(movement.reference, "Lote #505")

    def test_quick_assign_to_employee(self):
        """Testa atribuição direta de item em estoque ao colaborador."""
        url = reverse("inventory:quick-assign")
        data = {
            "item": self.item.pk,
            "employee": self.employee1.pk,
            "quantity": 2,
            "notes": "Entrega direta",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 8)

        assigned = InventoryItem.objects.get(
            name=self.item.name,
            assigned_employee=self.employee1,
            status=InventoryStatus.IN_USE,
        )
        self.assertEqual(assigned.quantity, 2)
        self.assertEqual(assigned.unit_price, self.item.unit_price)

    def test_assign_employee_deducts_stock_and_creates_assigned_item(self):
        url = reverse("inventory:item-assign", kwargs={"pk": self.item.pk})
        data = {
            "employee": self.employee1.pk,
            "quantity": 3,
            "notes": "Entrega para novo colaborador",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 7)

        assigned_item = InventoryItem.objects.get(
            name=self.item.name,
            assigned_employee=self.employee1,
            status=InventoryStatus.IN_USE,
        )
        self.assertEqual(assigned_item.quantity, 3)

    def test_return_assigned_item_to_stock(self):
        assigned_item = InventoryItem.objects.create(
            name="Mouse Ergonomico",
            category=self.category,
            brand="Logitech",
            model="MX Master 3",
            quantity=3,
            unit_price=Decimal("450.00"),
            status=InventoryStatus.IN_USE,
            assigned_employee=self.employee1,
            branch=self.branch,
        )

        url = reverse("inventory:item-return-stock", kwargs={"pk": assigned_item.pk})
        data = {
            "quantity": 2,
            "notes": "Devolução parcial",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        assigned_item.refresh_from_db()
        self.assertEqual(assigned_item.quantity, 1)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 12)

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

    def test_stock_list_and_collaborator_inventory_separation(self):
        """Garante que a aba Estoque exibe apenas itens em estoque e a aba Inventário exibe itens com colaboradores."""
        # Create assigned item for employee1
        assigned_item = InventoryItem.objects.create(
            name="Fone Bluetooth",
            category=self.category,
            brand="Sony",
            model="WH-1000XM4",
            quantity=1,
            unit_price=Decimal("1200.00"),
            status=InventoryStatus.IN_USE,
            assigned_employee=self.employee1,
            branch=self.branch,
        )

        # Aba Estoque: /estoque/
        stock_res = self.client.get(reverse("inventory:item-list"))
        self.assertEqual(stock_res.status_code, 200)
        self.assertIn(self.item, stock_res.context["objects"])
        self.assertNotIn(assigned_item, stock_res.context["objects"])

        # Aba Inventário: /estoque/inventario/
        inv_res = self.client.get(reverse("inventory:inventory-list"))
        self.assertEqual(inv_res.status_code, 200)
        self.assertIn(assigned_item, inv_res.context["objects"])
        self.assertNotIn(self.item, inv_res.context["objects"])

        # Busca no Inventário por colaborador
        search_res = self.client.get(reverse("inventory:inventory-list"), {"colaborador": self.employee1.pk})
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(assigned_item, search_res.context["objects"])

    def test_delete_inventory_item(self):
        url = reverse("inventory:item-delete", kwargs={"pk": self.item.pk})
        get_res = self.client.get(url)
        self.assertEqual(get_res.status_code, 200)

        post_res = self.client.post(url)
        self.assertEqual(post_res.status_code, 302)
        self.assertFalse(InventoryItem.objects.filter(pk=self.item.pk).exists())

    def test_discard_inventory_item(self):
        url = reverse("inventory:item-discard", kwargs={"pk": self.item.pk})
        get_res = self.client.get(url)
        self.assertEqual(get_res.status_code, 200)

        post_res = self.client.post(url, {"reason": "Equipamento queimado por sobretensão"})
        self.assertEqual(post_res.status_code, 302)

        self.item.refresh_from_db()
        self.assertEqual(self.item.status, InventoryStatus.DISCARDED)
        self.assertIn("Equipamento queimado por sobretensão", self.item.notes)
        movement = self.item.movements.latest("created_at")
        self.assertEqual(movement.reference, "Baixa por Descarte")
        self.assertEqual(movement.notes, "Equipamento queimado por sobretensão")



