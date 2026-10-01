from django import template

register = template.Library()

@register.filter(name='unfiltered_currency')
def unfiltered_currency(value):
    """Placeholder filter that returns the value unchanged.
    Used in dashboards to format currency without rounding.
    """
    return value
