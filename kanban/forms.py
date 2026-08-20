from django import forms

from core.forms import StyledModelForm
from kanban.models import KanbanTask


class KanbanTaskForm(StyledModelForm):
    """Formulário para criação e edição de Cards/Tarefas no quadro Kanban."""
    class Meta:
        model = KanbanTask
        fields = [
            "title",
            "description",
            "priority",
            "due_date",
            "assignee",
            "branch",
            "department",
            "status",
            "linked_service_order",
            "linked_purchase_order",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

