from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


class ServiceStatus(models.TextChoices):
    OPEN = "open", "Aberto"
    IN_PROGRESS = "in_progress", "Em Atendimento"
    DONE = "done", "Concluido"


class ServiceItemUsageType(models.TextChoices):
    EQUIPMENT = "equipment", "Equipamento Envolvido"
    PART = "part", "Peca/Item Consumido"


class ServiceOrder(TimeStampedModel):
    """Registro de suporte ou manutencao executada."""

    title = models.CharField("titulo", max_length=160)
    short_description = models.CharField("descricao curta", max_length=255)
    solution_description = models.TextField("solucao aplicada")
    attended_user = models.ForeignKey(
        "organization.Employee",
        on_delete=models.PROTECT,
        related_name="service_orders_as_customer",
        verbose_name="usuario atendido",
    )
    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.PROTECT,
        related_name="service_orders",
        verbose_name="setor",
    )
    branch = models.ForeignKey(
        "organization.Branch",
        on_delete=models.PROTECT,
        related_name="service_orders",
        verbose_name="filial",
    )
    technician = models.ForeignKey(
        "organization.Employee",
        on_delete=models.PROTECT,
        related_name="service_orders_as_technician",
        verbose_name="tecnico responsavel",
    )
    service_datetime = models.DateTimeField("data/hora do servico")
    status = models.CharField(
        "status",
        max_length=20,
        choices=ServiceStatus.choices,
        default=ServiceStatus.DONE,
    )

    class Meta:
        ordering = ("-service_datetime",)
        verbose_name = "ordem de servico"
        verbose_name_plural = "ordens de servico"

    def clean(self) -> None:
        if self.attended_user_id and self.department_id:
            if self.attended_user.department_id != self.department_id:
                raise ValidationError({"department": "O setor deve corresponder ao usuario atendido."})
        if self.department_id and self.branch_id and self.department.branch_id != self.branch_id:
            raise ValidationError({"branch": "A filial deve corresponder ao setor informado."})

    def save(self, *args, **kwargs):
        if self.attended_user_id and not self.department_id:
            self.department = self.attended_user.department
        if self.department_id and not self.branch_id:
            self.branch = self.department.branch
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class ServiceOrderItemUsage(TimeStampedModel):
    """Itens envolvidos ou consumidos durante o atendimento."""

    service_order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name="item_usages",
        verbose_name="ordem de servico",
    )
    item = models.ForeignKey(
        "inventory.InventoryItem",
        on_delete=models.PROTECT,
        related_name="service_usages",
        verbose_name="item",
    )
    usage_type = models.CharField(
        "tipo de uso",
        max_length=20,
        choices=ServiceItemUsageType.choices,
        default=ServiceItemUsageType.EQUIPMENT,
    )
    quantity = models.PositiveIntegerField("quantidade", default=1)
    stock_processed = models.BooleanField(default=False, editable=False)

    class Meta:
        verbose_name = "item utilizado no servico"
        verbose_name_plural = "itens utilizados no servico"

    def clean(self) -> None:
        if self.quantity <= 0:
            raise ValidationError({"quantity": "A quantidade precisa ser maior que zero."})

    def __str__(self) -> str:
        return f"{self.service_order.title} - {self.item.name}"
