from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


class PurchaseStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    APPROVED = "approved", "Aprovado"
    PURCHASED = "purchased", "Comprado"
    DELIVERED = "delivered", "Entregue"
    CANCELED = "canceled", "Cancelado"


class PurchaseOrder(TimeStampedModel):
    """Solicitacao ou ordem de compra."""

    title = models.CharField("titulo", max_length=160)
    branch = models.ForeignKey(
        "organization.Branch",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
        verbose_name="filial",
    )
    supplier = models.ForeignKey(
        "organization.Supplier",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
        verbose_name="fornecedor",
    )
    requester = models.ForeignKey(
        "organization.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_purchase_orders",
        verbose_name="solicitante",
    )
    purchase_date = models.DateField("data da compra")
    estimated_total = models.DecimalField(
        "valor estimado",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    actual_total = models.DecimalField(
        "valor real",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.PENDING,
    )
    invoice_link = models.URLField("link da nota fiscal", blank=True)
    invoice_file = models.FileField(
        "arquivo da nota fiscal",
        blank=True,
        upload_to="invoices/",
    )
    notes = models.TextField("observacoes", blank=True)
    inventory_processed = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ("-purchase_date", "-created_at")
        verbose_name = "ordem de compra"
        verbose_name_plural = "ordens de compra"

    def clean(self) -> None:
        if self.requester_id and self.requester.branch_id != self.branch_id:
            raise ValidationError(
                {"requester": "O solicitante precisa pertencer a mesma filial da compra."}
            )

    def __str__(self) -> str:
        return f"{self.title} - {self.get_status_display()}"


class PurchaseOrderItem(TimeStampedModel):
    """Item adquirido em uma ordem de compra."""

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="ordem de compra",
    )
    item_name = models.CharField("item/equipamento", max_length=150)
    category = models.ForeignKey(
        "organization.EquipmentCategory",
        on_delete=models.PROTECT,
        related_name="purchase_items",
        verbose_name="categoria",
    )
    model = models.CharField("modelo", max_length=120, blank=True)
    brand = models.CharField("marca", max_length=120, blank=True)
    quantity = models.PositiveIntegerField("quantidade", default=1)
    estimated_unit_price = models.DecimalField(
        "valor unitario estimado",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    actual_unit_price = models.DecimalField(
        "valor unitario real",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    inventory_item = models.ForeignKey(
        "inventory.InventoryItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_items",
        verbose_name="item de estoque vinculado",
    )

    class Meta:
        ordering = ("item_name",)
        verbose_name = "item da compra"
        verbose_name_plural = "itens da compra"

    @property
    def estimated_subtotal(self) -> Decimal:
        return self.quantity * self.estimated_unit_price

    @property
    def actual_subtotal(self) -> Decimal:
        return self.quantity * self.actual_unit_price

    def __str__(self) -> str:
        return self.item_name
