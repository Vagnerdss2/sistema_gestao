from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


class ServiceStatus(models.TextChoices):
    """
    Enumeração dos status de uma Ordem de Serviço / Atendimento Técnico:
    - OPEN: Aberto / Aguardando início do atendimento.
    - IN_PROGRESS: Em atendimento / análise pelo técnico de TI.
    - DONE: Concluído / Solução aplicada com sucesso.
    """
    OPEN = "open", "Aberto"
    IN_PROGRESS = "in_progress", "Em Atendimento"
    DONE = "done", "Concluido"


class ServiceItemUsageType(models.TextChoices):
    """
    Classificação do uso de itens em um atendimento:
    - EQUIPMENT: Equipamento que recebeu manutenção/suporte (não consome estoque).
    - PART: Peça, cabo ou insumo consumido/substituído (dá baixa no estoque).
    """
    EQUIPMENT = "equipment", "Equipamento Envolvido"
    PART = "part", "Peca/Item Consumido"


class ServiceOrder(TimeStampedModel):
    """
    Representa uma Ordem de Serviço / Atendimento de Suporte de TI.
    
    Registra data, horário, usuário solicitante/atendido, setor, filial,
    técnico executor, descrição do chamado, solução técnica aplicada e status.
    """

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
        """Valida se filial e setor coincidem com os dados cadastrais do colaborador atendido."""
        if self.attended_user_id and self.department_id:
            if self.attended_user.department_id != self.department_id:
                raise ValidationError({"department": "O setor deve corresponder ao usuario atendido."})
        if self.attended_user_id and self.branch_id:
            if self.attended_user.branch_id != self.branch_id:
                raise ValidationError({"branch": "A filial deve corresponder ao usuario atendido."})
        if (
            self.department_id
            and self.branch_id
            and not self.department.branches.filter(pk=self.branch_id).exists()
        ):
            raise ValidationError({"branch": "A filial precisa estar habilitada para o setor informado."})

    def save(self, *args, **kwargs):
        """Autopreencha setor e filial a partir do colaborador atendido se omitidos."""
        if self.attended_user_id and not self.department_id:
            self.department = self.attended_user.department
        if self.attended_user_id and not self.branch_id:
            self.branch = self.attended_user.branch
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class ServiceOrderItemUsage(TimeStampedModel):
    """
    Itens e insumos associados à Ordem de Serviço.
    
    Se o tipo for 'PART', o serviço do sistema dará baixa automática nas unidades do estoque.
    """

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

