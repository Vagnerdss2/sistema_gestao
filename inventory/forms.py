from django import forms

from core.forms import StyledForm, StyledModelForm
from inventory.models import InventoryItem, InventoryStatus
from organization.models import Employee


class InventoryItemForm(StyledModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "brand",
            "model",
            "serial_number",
            "asset_tag",
            "acquisition_date",
            "unit_price",
            "status",
            "quantity",
            "minimum_quantity",
            "branch",
            "assigned_employee",
            "notes",
        ]
        labels = {
            "name": "Nome do Item / Equipamento",
            "category": "Categoria",
            "brand": "Marca",
            "model": "Modelo",
            "serial_number": "Número de Série",
            "asset_tag": "Número de Patrimônio",
            "acquisition_date": "Data de Aquisição",
            "unit_price": "Valor Unitário do Item (R$)",
            "status": "Status",
            "quantity": "Quantidade em Estoque",
            "minimum_quantity": "Quantidade Mínima de Alerta",
            "branch": "Filial",
            "assigned_employee": "Colaborador Vinculado (se já em uso)",
            "notes": "Observações / Especificações Técnicas",
        }
        widgets = {
            "acquisition_date": forms.DateInput(attrs={"type": "date"}),
            "unit_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class AddStockForm(StyledForm):
    quantity = forms.IntegerField(
        label="Quantidade a Adicionar",
        min_value=1,
        initial=1,
        help_text="Informe o número de unidades a serem adicionadas ao estoque.",
    )
    acquisition_date = forms.DateField(
        label="Data de Aquisição / Entrada",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Data em que este lote/unidades foram adquiridos.",
    )
    unit_price = forms.DecimalField(
        label="Valor Unitário (R$)",
        required=False,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        help_text="Atualize o valor unitário do item se houver alteração de custo.",
    )
    reference = forms.CharField(
        label="Referência / Documento / NF",
        max_length=160,
        required=False,
        help_text="Ex: Nota Fiscal 1234, Lote de compra, Reposição de estoque.",
    )
    notes = forms.CharField(
        label="Observações da Entrada",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class QuickStockEntryForm(StyledForm):
    """Permite dar entrada de estoque selecionando um item já cadastrado."""

    item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.filter(assigned_employee__isnull=True).exclude(status=InventoryStatus.DISCARDED).order_by("name", "brand", "model"),
        label="Item / Equipamento Cadastrado",
        empty_label="Selecione o item já cadastrado para dar entrada...",
        help_text="Escolha um item já existente no catálogo para reabastecer o estoque.",
    )
    quantity = forms.IntegerField(
        label="Quantidade de Entrada",
        min_value=1,
        initial=1,
        help_text="Quantidade de novas unidades a adicionar ao estoque do item.",
    )
    acquisition_date = forms.DateField(
        label="Data de Aquisição / Entrada",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Data de compra ou entrada das unidades.",
    )
    unit_price = forms.DecimalField(
        label="Valor Unitário (R$)",
        required=False,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        help_text="Valor unitário das unidades que estão entrando (atualiza o cadastro do item se preenchido).",
    )
    reference = forms.CharField(
        label="Referência / Nota Fiscal / Lote",
        max_length=160,
        required=False,
        help_text="Ex: NF 45890, Pedido #123, Fornecedor X.",
    )
    notes = forms.CharField(
        label="Observações da Entrada",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class AssignEmployeeForm(StyledForm):
    item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.filter(assigned_employee__isnull=True, quantity__gt=0).exclude(status=InventoryStatus.DISCARDED).order_by("name", "brand", "model"),
        label="Item Disponível em Estoque",
        empty_label="Selecione o item disponível no estoque...",
        required=False,
        help_text="Selecione o item do estoque a ser entregue ao colaborador.",
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True).order_by("full_name"),
        label="Colaborador",
        empty_label="Selecione o colaborador...",
        help_text="Colaborador que receberá a(s) unidade(s) do equipamento.",
    )
    quantity = forms.IntegerField(
        label="Quantidade para dar baixa / entregar",
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

