from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Recupera um item de dicionario em templates."""

    if mapping is None:
        return []
    return mapping.get(key, [])
