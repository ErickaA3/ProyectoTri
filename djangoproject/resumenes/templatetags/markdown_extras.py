from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name='markdown_to_html')
def markdown_to_html(text):
    """Convierte markdown básico a HTML"""
    if not text:
        return ''
    
    # Convertir **texto** a <strong>texto</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convertir *texto* a <em>texto</em>
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Convertir # Título a <h3>Título</h3>
    text = re.sub(r'^# (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    
    # Convertir ## Subtítulo a <h4>Subtítulo</h4>
    text = re.sub(r'^## (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    
    # Convertir saltos de línea dobles a párrafos
    text = re.sub(r'\n\s*\n', '</p><p>', text)
    text = f'<p>{text}</p>'
    
    # Limpiar párrafos vacíos
    text = re.sub(r'<p></p>', '', text)
    
    return mark_safe(text)