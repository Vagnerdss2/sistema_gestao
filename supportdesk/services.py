from django.db import transaction

from inventory.models import MovementType, StockMovement
from supportdesk.models import ServiceItemUsageType, ServiceOrder


@transaction.atomic
def process_service_item_usages(service_order: ServiceOrder) -> None:
    """Aplica baixas de estoque para pecas consumidas no atendimento."""

    for usage in service_order.item_usages.select_related("item").filter(stock_processed=False):
        if usage.usage_type == ServiceItemUsageType.PART:
            StockMovement.register(
                item=usage.item,
                movement_type=MovementType.SERVICE_USAGE,
                quantity=usage.quantity,
                reference=f"OS #{service_order.pk}",
                notes="Baixa automatica gerada por item consumido em servico.",
                service_order=service_order,
            )

        usage.stock_processed = True
        usage.save(update_fields=["stock_processed", "updated_at"])
