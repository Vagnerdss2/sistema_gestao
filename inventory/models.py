from django.core.exceptions import ValidationError
from django.db import models, transaction

from core.models import TimeStampedModel


class InventoryStatus(models.TextChoices):
    IN_STOCK = "in_stock", "Em Estoque"
    IN_USE = "in_use", "Em Uso"
    IN_MAINTENANCE = "in_maintenance", "Em Manutencao"
    DISCARDED = "discarded", "Descartado"


class MovementType(models.TextChoices):
    ENTRY = "entry", "Entrada"
    EXIT = "exit", "Saida"
    ADJUSTMENT = "adjustment", "Ajuste"
    PURCHASE = "purchase", "Compra"
    SERVICE_USAGE = "service_usage", "Uso em Servico"


class InventoryItem(TimeStampedModel):
    """Item de estoque ou patrimonio controlado pelo time de TI."""

    name = models.CharField("nome", max_length=150)
    category = models.ForeignKey(
        "organization.EquipmentCategory",
        on_delete=models.PROTECT,
        related_name="inventory_items",
        verbose_name="categoria",
    )
    model = models.CharField("modelo", max_length=120, blank=True)
    brand = models.CharField("marca", max_length=120, blank=True)
    serial_number = models.CharField("numero de serie", max_length=120, blank=True)
    asset_tag = models.CharField("patrimonio", max_length=120, blank=True)
    status = models.CharField(
        "status",
        max_length=20,
        choices=InventoryStatus.choices,
        default=InventoryStatus.IN_STOCK,
    )
    quantity = models.PositiveIntegerField("quantidade em estoque", default=0)
    minimum_quantity = models.PositiveIntegerField("quantidade minima", default=0)
    branch = models.ForeignKey(
        "organization.Branch",
        on_delete=models.PROTECT,
        related_name="inventory_items",
        verbose_name="filial",
    )
    assigned_employee = models.ForeignKey(
        "organization.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_inventory_items",
        verbose_name="colaborador vinculado",
    )
    notes = models.TextField("observacoes", blank=True)

    class Meta:
        ordering = ("name", "brand", "model")
        verbose_name = "item de estoque"
        verbose_name_plural = "itens de estoque"
        constraints = [
            models.UniqueConstraint(
                fields=("serial_number",),
                condition=~models.Q(serial_number=""),
                name="unique_non_blank_serial_number",
            ),
            models.UniqueConstraint(
                fields=("asset_tag",),
                condition=~models.Q(asset_tag=""),
                name="unique_non_blank_asset_tag",
            ),
        ]

    def clean(self) -> None:
        if self.assigned_employee and self.assigned_employee.branch_id != self.branch_id:
            raise ValidationError(
                {"assigned_employee": "O colaborador precisa pertencer a mesma filial do item."}
            )

    @property
    def is_below_minimum(self) -> bool:
        return self.quantity <= self.minimum_quantity

    def __str__(self) -> str:
        return f"{self.name} - {self.brand} {self.model}".strip()


class StockMovement(TimeStampedModel):
    """Historico imutavel de movimentacoes de estoque."""

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="movements",
        verbose_name="item",
    )
    movement_type = models.CharField(
        "tipo de movimentacao",
        max_length=20,
        choices=MovementType.choices,
    )
    quantity = models.PositiveIntegerField("quantidade")
    reference = models.CharField("referencia", max_length=160, blank=True)
    notes = models.TextField("observacoes", blank=True)
    purchase_order = models.ForeignKey(
        "procurement.PurchaseOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="compra",
    )
    service_order = models.ForeignKey(
        "supportdesk.ServiceOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="ordem de servico",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "movimentacao de estoque"
        verbose_name_plural = "movimentacoes de estoque"

    def __str__(self) -> str:
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.quantity})"

    @classmethod
    def register(
        cls,
        *,
        item: InventoryItem,
        movement_type: str,
        quantity: int,
        reference: str = "",
        notes: str = "",
        purchase_order=None,
        service_order=None,
    ) -> "StockMovement":
        if quantity <= 0:
            raise ValidationError("A quantidade da movimentacao precisa ser positiva.")

        delta = quantity
        if movement_type in {MovementType.EXIT, MovementType.SERVICE_USAGE}:
            delta = -quantity

        with transaction.atomic():
            locked_item = InventoryItem.objects.select_for_update().get(pk=item.pk)
            new_quantity = locked_item.quantity + delta
            if new_quantity < 0:
                raise ValidationError("Estoque insuficiente para realizar a movimentacao.")

            locked_item.quantity = new_quantity
            if locked_item.quantity == 0 and locked_item.status == InventoryStatus.IN_STOCK:
                locked_item.status = InventoryStatus.IN_USE if locked_item.assigned_employee_id else InventoryStatus.IN_STOCK
            locked_item.save(update_fields=["quantity", "status", "updated_at"])

            return cls.objects.create(
                item=locked_item,
                movement_type=movement_type,
                quantity=quantity,
                reference=reference,
                notes=notes,
                purchase_order=purchase_order,
                service_order=service_order,
            )
