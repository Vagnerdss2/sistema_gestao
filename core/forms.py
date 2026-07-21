from django import forms


class StyledModelForm(forms.ModelForm):
    """Aplica classes utilitarias padrao aos campos do sistema."""

    default_class = (
        "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
        "shadow-sm focus:border-sky-500 focus:outline-none focus:ring-2 "
        "focus:ring-sky-200"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            existing_class = widget.attrs.get("class", "")
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "h-4 w-4 rounded border-slate-300 text-sky-600"
            else:
                widget.attrs["class"] = f"{existing_class} {self.default_class}".strip()
