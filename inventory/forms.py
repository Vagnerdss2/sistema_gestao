from django import forms

from core.forms import StyledForm, StyledModelForm
from inventory.models import InventoryItem
from organization.models import Employee


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


class AddStockForm(StyledForm):
    quantity = forms.IntegerField(
        label="Quantidade a adicionar",
        min_value=1,
        initial=1,
        help_text="Informe o número de unidades a serem adicionadas ao estoque.",
    )
    reference = forms.CharField(
        label="Referência / Documento",
        max_length=160,
        required=False,
        help_text="Ex: Nota Fiscal 1234, Lote de compra, Reposição de estoque.",
    )
    notes = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class AssignEmployeeForm(StyledForm):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        label="Colaborador",
        empty_label="Selecione o colaborador...",
        help_text="Colaborador que receberá a(s) unidade(s) do item.",
    )
    quantity = forms.IntegerField(
        label="Quantidade para dar baixa",
        min_value=1,
        initial=1,
        help_text="Quantidade de unidades retiradas do estoque para este colaborador.",
    )
    notes = forms.CharField(
        label="Observações / Termo de Entrega",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ReturnStockForm(StyledForm):
    quantity = forms.IntegerField(
        label="Quantidade a devolver",
        min_value=1,
        initial=1,
        help_text="Quantidade de unidades a serem devolvidas ao estoque geral.",
    )
    notes = forms.CharField(
        label="Observações / Motivo da Devolução",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class DiscardEquipmentForm(StyledForm):
    reason = forms.CharField(
        label="Motivo do Descarte / Laudo Técnico",
        required=True,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Descreva a justificativa para o descarte do equipamento (ex: Dano irreparável, Obsolescência, Queima de componente)...",
            }
        ),
        help_text="Informe o motivo técnico ou operacional para descartar este equipamento.",
    )

