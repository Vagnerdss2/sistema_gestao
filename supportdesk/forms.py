from django import forms
from django.forms import inlineformset_factory

from core.forms import StyledModelForm
from supportdesk.models import ServiceOrder, ServiceOrderItemUsage


class ServiceOrderForm(StyledModelForm):
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
    class Meta:
        model = ServiceOrderItemUsage
        fields = ["item", "usage_type", "quantity"]


ServiceOrderItemUsageFormSet = inlineformset_factory(
    ServiceOrder,
    ServiceOrderItemUsage,
    form=ServiceOrderItemUsageForm,
    extra=1,
    can_delete=True,
)
