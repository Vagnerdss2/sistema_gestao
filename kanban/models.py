from django.db import models

from core.models import TimeStampedModel


class TaskPriority(models.TextChoices):
    LOW = "low", "Baixa"
    MEDIUM = "medium", "Media"
    HIGH = "high", "Alta"
    URGENT = "urgent", "Urgente"


class TaskStatus(models.TextChoices):
    TODO = "todo", "A Fazer"
    IN_PROGRESS = "in_progress", "Em Andamento"
    WAITING = "waiting", "Pendente / Aguardando"
    DONE = "done", "Concluido"


class KanbanTask(TimeStampedModel):
    """Card do quadro Kanban operacional."""

    title = models.CharField("titulo", max_length=160)
    description = models.TextField("descricao detalhada")
    priority = models.CharField(
        "prioridade",
        max_length=10,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
    )
    due_date = models.DateField("prazo", null=True, blank=True)
    assignee = models.ForeignKey(
        "organization.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kanban_tasks",
        verbose_name="responsavel",
    )
    branch = models.ForeignKey(
        "organization.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kanban_tasks",
        verbose_name="filial",
    )
    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kanban_tasks",
        verbose_name="setor",
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )
    sort_order = models.PositiveIntegerField("ordem", default=0)
    linked_service_order = models.ForeignKey(
        "supportdesk.ServiceOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kanban_tasks",
        verbose_name="ordem de servico vinculada",
    )
    linked_purchase_order = models.ForeignKey(
        "procurement.PurchaseOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kanban_tasks",
        verbose_name="compra vinculada",
    )

    class Meta:
        ordering = ("status", "sort_order", "-created_at")
        verbose_name = "tarefa do kanban"
        verbose_name_plural = "tarefas do kanban"

    def __str__(self) -> str:
        return self.title
