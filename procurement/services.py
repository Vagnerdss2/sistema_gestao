from decimal import Decimal

from django.db import transaction

from inventory.models import InventoryItem, MovementType, StockMovement
from procurement.models import PurchaseOrder, PurchaseStatus


@transaction.atomic
def sync_purchase_order_to_inventory(purchase_order: PurchaseOrder) -> None:
    """Integra a compra ao estoque quando a entrega e confirmada."""

    if (
        purchase_order.status != PurchaseStatus.DELIVERED
        or purchase_order.inventory_processed
    ):
        return

    for item in purchase_order.items.select_related("category", "inventory_item"):
        inventory_item = item.inventory_item
        if inventory_item is None:
            inventory_item = InventoryItem.objects.create(
                name=item.item_name,
                category=item.category,
                model=item.model,
                brand=item.brand,
                quantity=0,
                minimum_quantity=0,
                branch=purchase_order.branch,
            )
            item.inventory_item = inventory_item
            item.save(update_fields=["inventory_item", "updated_at"])

        StockMovement.register(
            item=inventory_item,
            movement_type=MovementType.PURCHASE,
            quantity=item.quantity,
            reference=f"Compra #{purchase_order.pk}",
            notes="Entrada automatica a partir de compra entregue.",
            purchase_order=purchase_order,
        )

    purchase_order.inventory_processed = True
    purchase_order.save(update_fields=["inventory_processed", "updated_at"])


def refresh_purchase_totals(purchase_order: PurchaseOrder) -> None:
    """Recalcula os totais estimado e real da compra com base nos itens se houver subtotais informados."""

    items = list(purchase_order.items.all())
    if not items:
        return

    items_estimated_total = sum((item.estimated_subtotal for item in items), Decimal("0.00"))
    items_actual_total = sum((item.actual_subtotal for item in items), Decimal("0.00"))

    fields_to_update = []
    if items_estimated_total > Decimal("0.00"):
        purchase_order.estimated_total = items_estimated_total
        fields_to_update.append("estimated_total")

    if items_actual_total > Decimal("0.00"):
        purchase_order.actual_total = items_actual_total
        fields_to_update.append("actual_total")

    if fields_to_update:
        fields_to_update.append("updated_at")
        purchase_order.save(update_fields=fields_to_update)

