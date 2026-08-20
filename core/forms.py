from django import forms


class StyledForm(forms.Form):
    """
    Formulário base não vinculado a modelos com estilização Tailwind CSS pré-configurada.
    
    Percorre todos os campos definidos no formulário durante a inicialização e adiciona
    as classes utilitárias CSS adequadas (bordas, arredondamento, sombras, estados de foco),
    garantindo consistência visual em todo o sistema.
    """

    # Classes utilitárias padrão do Tailwind para inputs de texto, selects e datas
    default_class = (
        "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
        "shadow-sm focus:border-sky-500 focus:outline-none focus:ring-2 "
        "focus:ring-sky-200"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Itera por todos os campos do formulário para aplicar o estilo apropriado
        for field in self.fields.values():
            widget = field.widget
            existing_class = widget.attrs.get("class", "")
            # Checkbox recebe estilo diferenciado (quadrado pequeno com cor de destaque)
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
            else:
                # Demais campos recebem o estilo padrão de campo de texto/seleção
                widget.attrs["class"] = f"{existing_class} {self.default_class}".strip()


class StyledModelForm(forms.ModelForm):
    """
    Formulário base vinculado a Modelos Django com estilização Tailwind CSS pré-configurada.
    
    Aplica automaticamente as classes CSS do padrão de design system em todos os campos
    gerados dinamicamente a partir dos modelos (ModelForm).
    """

    default_class = (
        "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
        "shadow-sm focus:border-sky-500 focus:outline-none focus:ring-2 "
        "focus:ring-sky-200"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Itera por todos os campos do ModelForm aplicando as classes de estilo
        for field in self.fields.values():
            widget = field.widget
            existing_class = widget.attrs.get("class", "")
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
            else:
                widget.attrs["class"] = f"{existing_class} {self.default_class}".strip()

