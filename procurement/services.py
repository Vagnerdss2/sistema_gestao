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
    """Recalcula os totais estimado e real da compra com base nos itens."""

    estimated_total = Decimal("0.00")
    actual_total = Decimal("0.00")
    for item in purchase_order.items.all():
        estimated_total += item.estimated_subtotal
        actual_total += item.actual_subtotal

    purchase_order.estimated_total = estimated_total
    purchase_order.actual_total = actual_total
    purchase_order.save(update_fields=["estimated_total", "actual_total", "updated_at"])
