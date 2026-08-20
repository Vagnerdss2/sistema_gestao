from django import forms
from django.forms import inlineformset_factory

from core.forms import StyledModelForm
from supportdesk.models import ServiceOrder, ServiceOrderItemUsage


class ServiceOrderForm(StyledModelForm):
    """Formulário principal para registro e atualização de Ordens de Serviço de TI."""
    class Meta:
        model = ServiceOrder
        fields = [
            "title",
            "short_description",
            "solution_description",
            "attended_user",
            "department",
            "branch",
            "technician",
            "service_datetime",
            "status",
        ]
        widgets = {
            "solution_description": forms.Textarea(attrs={"rows": 4}),
            "service_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ServiceOrderItemUsageForm(StyledModelForm):
    """Formulário individual para cada linha de item/peça utilizada no atendimento."""
    class Meta:
        model = ServiceOrderItemUsage
        fields = ["item", "usage_type", "quantity"]


# Formset dinâmico que permite associar múltiplos itens/peças a uma única Ordem de Serviço
ServiceOrderItemUsageFormSet = inlineformset_factory(
    ServiceOrder,
    ServiceOrderItemUsage,
    form=ServiceOrderItemUsageForm,
    extra=1,
    can_delete=True,
)

