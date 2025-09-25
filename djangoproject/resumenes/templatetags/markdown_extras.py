from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name='markdown_to_html')
def markdown_to_html(text):
    """Convierte markdown básico a HTML con mejor formateo"""
    if not text:
        return ''
    
    # Escapar caracteres HTML peligrosos primero
    text = str(text)
    
    # Convertir **texto** a <strong>texto</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convertir *texto* a <em>texto</em>  
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    
    # Convertir # Título a <h3>Título</h3>
    text = re.sub(r'^#{1}\s+(.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    
    # Convertir ## Subtítulo a <h4>Subtítulo</h4>
    text = re.sub(r'^#{2}\s+(.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    
    # Convertir ### Subtítulo a <h5>Subtítulo</h5>
    text = re.sub(r'^#{3}\s+(.*?)$', r'<h5>\1</h5>', text, flags=re.MULTILINE)
    
    # Procesar listas de puntos - MANEJAR AMBOS TIPOS
    lines = text.split('\n')
    processed_lines = []
    in_list = False
    current_list_type = None
    
    for line in lines:
        stripped_line = line.strip()
        
        # Detectar elementos de lista
        if stripped_line.startswith('- ') or re.match(r'^\d+\.\s', stripped_line):
            list_type = 'ul' if stripped_line.startswith('- ') else 'ol'
            
            # Si no estamos en lista o cambia el tipo, abrir nueva lista
            if not in_list or current_list_type != list_type:
                if in_list:  # Cerrar lista anterior si existe
                    processed_lines.append(f'</{current_list_type}>')
                processed_lines.append(f'<{list_type}>')
                in_list = True
                current_list_type = list_type
            
            # Remover el marcador y agregar como elemento de lista
            if stripped_line.startswith('- '):
                content = stripped_line[2:].strip()
            else:
                content = re.sub(r'^\d+\.\s', '', stripped_line).strip()
            
            processed_lines.append(f'<li>{content}</li>')
        else:
            # Cerrar lista si estaba abierta
            if in_list:
                processed_lines.append(f'</{current_list_type}>')
                in_list = False
                current_list_type = None
            
            # Agregar línea normal
            if stripped_line:
                processed_lines.append(f'<p>{stripped_line}</p>')
            else:
                processed_lines.append('')
    
    # Cerrar lista final si quedó abierta
    if in_list:
        processed_lines.append(f'</{current_list_type}>')
    
    # Unir todas las líneas
    result = '\n'.join(processed_lines)
    
    # Limpiar párrafos vacíos y espacios extra
    result = re.sub(r'<p></p>', '', result)
    result = re.sub(r'<p>\s*</p>', '', result)
    result = re.sub(r'\n\s*\n', '\n', result)
    
    return mark_safe(result)