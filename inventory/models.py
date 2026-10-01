from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction

from core.models import TimeStampedModel


class InventoryStatus(models.TextChoices):
    """
    Enumeração dos status operacionais possíveis de um item no inventário:
    - IN_STOCK: Disponível no estoque geral para uso ou atribuição.
    - IN_USE: Em uso ativo por um colaborador ou setor.
    - IN_MAINTENANCE: Em manutenção preventiva, corretiva ou conserto técnico.
    - DISCARDED: Descartado / Baixado definitivamente por obsolescência, avaria ou perda.
    """
    IN_STOCK = "in_stock", "Em Estoque"
    IN_USE = "in_use", "Em Uso"
    IN_MAINTENANCE = "in_maintenance", "Em Manutenção"
    DISCARDED = "discarded", "Descartado"


class MovementType(models.TextChoices):
    """
    Enumeração dos tipos de movimentações de estoque registradas:
    - ENTRY: Entrada manual ou reposição de estoque.
    - EXIT: Saída manual ou baixa de estoque.
    - ADJUSTMENT: Ajuste de contagem/inventário físico.
    - PURCHASE: Entrada decorrente de compra / recebimento de mercadoria.
    - SERVICE_USAGE: Saída consumida na execução de uma ordem de serviço.
    """
    ENTRY = "entry", "Entrada"
    EXIT = "exit", "Saída"
    ADJUSTMENT = "adjustment", "Ajuste"
    PURCHASE = "purchase", "Compra"
    SERVICE_USAGE = "service_usage", "Uso em Serviço"


class InventoryItem(TimeStampedModel):
    """
    Representa um item, ativo patrimonial ou equipamento controlado pelo time de TI.
    
    Pode representar tanto itens estocados no almoxarifado geral quanto itens
    alocados nominalmente a colaboradores (Inventário).
    """

    name = models.CharField("nome", max_length=150)
    category = models.ForeignKey(
        "organization.EquipmentCategory",
        on_delete=models.PROTECT,
        related_name="inventory_items",
        verbose_name="categoria",
    )
    model = models.CharField("modelo", max_length=120, blank=True)
    brand = models.CharField("marca", max_length=120, blank=True)
    serial_number = models.CharField("número de série", max_length=120, blank=True)
    asset_tag = models.CharField("patrimônio", max_length=120, blank=True)
    # Data em que o equipamento ou lote foi adquirido
    acquisition_date = models.DateField("data de aquisição", null=True, blank=True)
    # Valor unitário do item em Reais (R$)
    unit_price = models.DecimalField(
        "valor do item (R$)",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=InventoryStatus.choices,
        default=InventoryStatus.IN_STOCK,
    )
    quantity = models.PositiveIntegerField("quantidade em estoque", default=0)
    minimum_quantity = models.PositiveIntegerField("quantidade mínima", default=0)
    branch = models.ForeignKey(
        "organization.Branch",
        on_delete=models.PROTECT,
        related_name="inventory_items",
        verbose_name="filial",
    )
    # Colaborador que está com a posse física do equipamento (se nulo, item está no estoque geral)
    assigned_employee = models.ForeignKey(
        "organization.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_inventory_items",
        verbose_name="colaborador vinculado",
    )
    notes = models.TextField("observações", blank=True)

    class Meta:
        ordering = ("name", "brand", "model")
        verbose_name = "item de estoque"
        verbose_name_plural = "itens de estoque"
        constraints = [
            # Garante que números de série não sejam duplicados quando preenchidos
            models.UniqueConstraint(
                fields=("serial_number",),
                condition=~models.Q(serial_number=""),
                name="unique_non_blank_serial_number",
            ),
            # Garante que números de patrimônio não sejam duplicados quando preenchidos
            models.UniqueConstraint(
                fields=("asset_tag",),
                condition=~models.Q(asset_tag=""),
                name="unique_non_blank_asset_tag",
            ),
        ]

    def clean(self) -> None:
        """Validação: se o item for vinculado a um colaborador, ambos devem pertencer à mesma filial."""
        if self.assigned_employee and self.assigned_employee.branch_id != self.branch_id:
            raise ValidationError(
                {"assigned_employee": "O colaborador precisa pertencer a mesma filial do item."}
            )

    @property
    def is_below_minimum(self) -> bool:
        """Indica se a quantidade atual atingiu ou está abaixo do limite de segurança configurado."""
        return self.quantity <= self.minimum_quantity

    @property
    def total_value(self) -> Decimal:
        """Calcula o valor financeiro total do estoque deste item (quantidade * preço unitário)."""
        return (self.unit_price or Decimal("0.00")) * (self.quantity or 0)

    @property
    def display_full_name(self) -> str:
        """Formata uma identificação completa com Nome, Marca, Modelo e Série/Patrimônio para selects."""
        parts = [self.name]
        extra = f"{self.brand} {self.model}".strip()
        if extra:
            parts.append(f"({extra})")
        if self.serial_number:
            parts.append(f"[S/N: {self.serial_number}]")
        elif self.asset_tag:
            parts.append(f"[Patr: {self.asset_tag}]")
        return " ".join(parts)

    def __str__(self) -> str:
        return f"{self.name} - {self.brand} {self.model}".strip()


class StockMovement(TimeStampedModel):
    """
    Histórico imutável de movimentações de estoque (Livro de Entradas e Saídas).
    
    Registra cada alteração quantitativa, data de aquisição, valor, motivo,
    referência de documento (Nota Fiscal/Lote) e vínculos com Ordens de Serviço.
    """

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="movements",
        verbose_name="item",
    )
    movement_type = models.CharField(
        "tipo de movimentação",
        max_length=20,
        choices=MovementType.choices,
    )
    quantity = models.PositiveIntegerField("quantidade")
    unit_price = models.DecimalField(
        "valor unitário (R$)",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    acquisition_date = models.DateField("data de aquisição", null=True, blank=True)
    reference = models.CharField("referência", max_length=160, blank=True)
    notes = models.TextField("observações", blank=True)
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
        verbose_name="ordem de serviço",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "movimentação de estoque"
        verbose_name_plural = "movimentações de estoque"

    def __str__(self) -> str:
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.quantity})"

    @property
    def total_value(self) -> Decimal:
        """Calcula o valor financeiro movimentado nesta operação."""
        price = self.unit_price or self.item.unit_price or Decimal("0.00")
        return price * self.quantity

    @classmethod
    def register(
        cls,
        *,
        item: InventoryItem,
        movement_type: str,
        quantity: int,
        unit_price=None,
        acquisition_date=None,
        reference: str = "",
        notes: str = "",
        purchase_order=None,
        service_order=None,
    ) -> "StockMovement":
        """
        Método centralizador atômico para registro seguro de movimentações de estoque.
        
        Executa:
        1. Validação de quantidade estritamente positiva.
        2. Bloqueio pessimista de linha (select_for_update) para evitar condições de corrida (race conditions).
        3. Recálculo e validação do saldo de estoque.
        4. Atualização de preço unitário e data de aquisição do item se informados.
        5. Criação do registro auditável de StockMovement.
        """
        if quantity <= 0:
            raise ValidationError("A quantidade da movimentação precisa ser positiva.")

        # Determina se a operação soma ou subtrai do saldo do item
        delta = quantity
        if movement_type in {MovementType.EXIT, MovementType.SERVICE_USAGE}:
            delta = -quantity

        with transaction.atomic():
            # Bloqueio pessimista da linha do item no banco
            locked_item = InventoryItem.objects.select_for_update().get(pk=item.pk)
            new_quantity = locked_item.quantity + delta
            if new_quantity < 0:
                raise ValidationError("Estoque insuficiente para realizar a movimentação.")

            locked_item.quantity = new_quantity
            if locked_item.quantity == 0 and locked_item.status == InventoryStatus.IN_STOCK:
                locked_item.status = InventoryStatus.IN_USE if locked_item.assigned_employee_id else InventoryStatus.IN_STOCK

            update_fields = ["quantity", "status", "updated_at"]
            if unit_price is not None:
                locked_item.unit_price = unit_price
                update_fields.append("unit_price")
            if acquisition_date is not None:
                locked_item.acquisition_date = acquisition_date
                update_fields.append("acquisition_date")

            locked_item.save(update_fields=update_fields)

            # Cria e retorna o registro histórico da movimentação
            return cls.objects.create(
                item=locked_item,
                movement_type=movement_type,
                quantity=quantity,
                unit_price=unit_price if unit_price is not None else locked_item.unit_price,
                acquisition_date=acquisition_date if acquisition_date is not None else locked_item.acquisition_date,
                reference=reference,
                notes=notes,
                purchase_order=purchase_order,
                service_order=service_order,
            )

