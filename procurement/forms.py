from django import forms
from django.forms import inlineformset_factory

from core.forms import StyledModelForm
from procurement.models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderForm(StyledModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            "title",
            "branch",
            "supplier",
            "requester",
            "purchase_date",
            "estimated_total",
            "actual_total",
            "status",
            "invoice_link",
            "invoice_file",
            "notes",
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class PurchaseOrderItemForm(StyledModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = [
            "item_name",
            "category",
            "model",
            "brand",
            "quantity",
            "estimated_unit_price",
            "actual_unit_price",
            "inventory_item",
        ]


PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1,
    can_delete=True,
)
