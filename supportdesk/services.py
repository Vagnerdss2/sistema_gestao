from django.db import transaction

from inventory.models import MovementType, StockMovement
from supportdesk.models import ServiceItemUsageType, ServiceOrder


@transaction.atomic
def process_service_item_usages(service_order: ServiceOrder) -> None:
    """
    Processa as baixas automáticas de estoque para peças e insumos consumidos na Ordem de Serviço.
    
    Para cada item vinculado à OS com tipo PART (Peça/Insumo) e que ainda não tenha sido processado:
    1. Registra a movimentação de saída do tipo SERVICE_USAGE com bloqueio de concorrência.
    2. Vincula a movimentação à Ordem de Serviço executada.
    3. Marca a flag stock_processed como True para evitar baixas duplicadas em edições futuras.
    """

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

        # Marca como processado no banco
        usage.stock_processed = True
        usage.save(update_fields=["stock_processed", "updated_at"])

