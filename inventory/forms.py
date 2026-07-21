from django import forms

from core.forms import StyledModelForm
from inventory.models import InventoryItem


class InventoryItemForm(StyledModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "model",
            "brand",
            "serial_number",
            "asset_tag",
            "status",
            "quantity",
            "minimum_quantity",
            "branch",
            "assigned_employee",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
