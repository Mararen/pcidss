from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Accede a un dict con clave dinámica en templates."""
    return dictionary.get(key, 0)


@register.filter
def saq_chip_class(saq):
    """Devuelve la clase CSS del chip según el tipo de SAQ."""
    return {
        'A':           'saq-chip--a',
        'AEP':         'saq-chip--aep',
        'B':           'saq-chip--b',
        'BIP':         'saq-chip--bip',
        'C':           'saq-chip--c',
        'CTV':         'saq-chip--ctv',
        'D-COMERCIO':  'saq-chip--d-comercio',
        'D-PROVEEDOR': 'saq-chip--d-proveedor',
    }.get(saq, '')

@register.filter
def split(value, arg):
    """Divide un string por el separador dado. Uso: {{ value|split:"," }}"""
    if not value:
        return []
    return [v.strip() for v in value.split(arg) if v.strip()]