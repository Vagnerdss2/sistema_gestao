from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Recupera um item de dicionario em templates."""
    if mapping is None:
        return []
    return mapping.get(key, [])


@register.filter
def currency(value):
    """Formata um valor numerico como moeda brasileira (R$ 1.234,56)."""
    if value is None or value == "":
        return "R$ 0,00"
    try:
        if isinstance(value, str):
            clean_str = value.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
            val = Decimal(clean_str)
        elif isinstance(value, (int, float)):
            val = Decimal(str(value))
        elif isinstance(value, Decimal):
            val = value
        else:
            val = Decimal(str(value))

        formatted = f"{val:,.2f}"
        main_part, dec_part = formatted.split(".")
        main_part = main_part.replace(",", ".")
        return f"R$ {main_part},{dec_part}"
    except Exception:
        return f"R$ {value}"


@register.filter
def multiply(value, arg):
    """Multiplica dois valores com seguranca."""
    try:
        val1 = Decimal(str(value or 0))
        val2 = Decimal(str(arg or 0))
        return val1 * val2
    except Exception:
        return Decimal("0.00")
