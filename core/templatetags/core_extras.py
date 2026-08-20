from decimal import Decimal
from django import template

# Instância da biblioteca de template tags customizadas do Django
register = template.Library()


@register.filter
def get_item(mapping, key):
    """
    Filtro de template para recuperar valores de um dicionário por chave dinâmica.
    
    Uso no template: {{ meu_dicionario|get_item:minha_chave }}
    Retorna uma lista vazia caso o mapeamento não exista ou a chave não seja encontrada.
    """
    if mapping is None:
        return []
    return mapping.get(key, [])


@register.filter
def currency(value):
    """
    Filtro de template para formatar valores numéricos no padrão de moeda Real Brasileiro (R$).
    
    Converte valores Decimal, float ou string numérica para a notação brasileira:
    Exemplo: 1234.50 -> R$ 1.234,50
    Uso no template: {{ item.unit_price|currency }}
    """
    if value is None or value == "":
        return "R$ 0,00"
    try:
        if isinstance(value, str):
            # Limpa caracteres não numéricos caso receba string formatada
            clean_str = value.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
            val = Decimal(clean_str)
        elif isinstance(value, (int, float)):
            val = Decimal(str(value))
        elif isinstance(value, Decimal):
            val = value
        else:
            val = Decimal(str(value))

        # Formata com separador de milhar americano (,) e decimal (.)
        formatted = f"{val:,.2f}"
        # Converte para a convenção brasileira (milhar com . e decimal com ,)
        main_part, dec_part = formatted.split(".")
        main_part = main_part.replace(",", ".")
        return f"R$ {main_part},{dec_part}"
    except Exception:
        return f"R$ {value}"


@register.filter
def multiply(value, arg):
    """
    Filtro de template para multiplicar dois valores com precisão decimal e tratamento de erros.
    
    Uso no template: {{ item.quantity|multiply:item.unit_price|currency }}
    """
    try:
        val1 = Decimal(str(value or 0))
        val2 = Decimal(str(arg or 0))
        return val1 * val2
    except Exception:
        return Decimal("0.00")

