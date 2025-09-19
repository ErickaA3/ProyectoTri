# esquemas/utils.py
import os
import json
from django.conf import settings

def extraer_texto_archivo(archivo):
    """
    Extrae texto de diferentes tipos de archivo
    """
    nombre_archivo = archivo.name.lower()
    
    if nombre_archivo.endswith('.txt'):
        return extraer_texto_txt(archivo)
    elif nombre_archivo.endswith('.pdf'):
        return "Contenido de ejemplo del PDF. Por favor instala PyPDF2 para funcionalidad completa."
    elif nombre_archivo.endswith(('.doc', '.docx')):
        return "Contenido de ejemplo del documento Word. Por favor instala python-docx para funcionalidad completa."
    else:
        raise ValueError("Formato de archivo no soportado")

def extraer_texto_txt(archivo):
    """Extrae texto de archivos TXT"""
    try:
        return archivo.read().decode('utf-8')
    except UnicodeDecodeError:
        try:
            archivo.seek(0)
            return archivo.read().decode('latin-1')
        except Exception as e:
            raise ValueError(f"Error al leer archivo TXT: {str(e)}")

def generar_esquema_openai(texto, tipo_esquema):
    """
    Genera un esquema usando OpenAI GPT - VERSION SIMPLIFICADA PARA TESTING
    """
    # Para testing sin OpenAI, devolver datos de ejemplo
    if tipo_esquema == 'jerarquico':
        return {
            "titulo": "Esquema Generado",
            "nodos": [
                {
                    "texto": "Punto Principal 1",
                    "nivel": 1,
                    "orden": 0,
                    "hijos": [
                        {
                            "texto": "Subpunto 1.1",
                            "nivel": 2,
                            "orden": 0,
                            "hijos": [
                                {
                                    "texto": "Detalle 1.1.1",
                                    "nivel": 3,
                                    "orden": 0
                                }
                            ]
                        }
                    ]
                },
                {
                    "texto": "Punto Principal 2",
                    "nivel": 1,
                    "orden": 1,
                    "hijos": [
                        {
                            "texto": "Subpunto 2.1",
                            "nivel": 2,
                            "orden": 0
                        }
                    ]
                }
            ]
        }
    
    elif tipo_esquema == 'conceptual':
        return {
            "titulo": "Mapa Conceptual Generado",
            "concepto_central": "Concepto Principal",
            "conceptos": [
                {
                    "texto": "Concepto Relacionado 1",
                    "descripcion": "Descripción del primer concepto",
                    "es_central": False
                },
                {
                    "texto": "Concepto Relacionado 2", 
                    "descripcion": "Descripción del segundo concepto",
                    "es_central": False
                }
            ]
        }
    
    elif tipo_esquema == 'cronologico':
        return {
            "titulo": "Línea de Tiempo Generada",
            "eventos": [
                {
                    "fecha": "2020",
                    "titulo": "Evento Importante 1",
                    "descripcion": "Descripción del primer evento",
                    "orden": 0
                },
                {
                    "fecha": "2021",
                    "titulo": "Evento Importante 2",
                    "descripcion": "Descripción del segundo evento", 
                    "orden": 1
                }
            ]
        }

def crear_nodos_desde_json(esquema, datos_json):
    """
    Crea nodos en la base de datos desde JSON para esquemas jerárquicos
    """
    from .models import NodoEsquema
    
    def crear_nodo_recursivo(datos_nodo, padre=None):
        nodo = NodoEsquema.objects.create(
            esquema=esquema,
            texto=datos_nodo['texto'],
            nivel=datos_nodo['nivel'],
            orden=datos_nodo.get('orden', 0),
            padre=padre
        )
        
        # Crear nodos hijos si existen
        if 'hijos' in datos_nodo:
            for hijo_datos in datos_nodo['hijos']:
                crear_nodo_recursivo(hijo_datos, nodo)
        
        return nodo
    
    # Crear todos los nodos desde el JSON
    for nodo_datos in datos_json.get('nodos', []):
        crear_nodo_recursivo(nodo_datos)

def crear_eventos_desde_json(esquema, datos_json):
    """
    Crea eventos en la base de datos desde JSON para líneas de tiempo
    """
    from .models import EventoTimeline
    
    for evento_datos in datos_json.get('eventos', []):
        EventoTimeline.objects.create(
            esquema=esquema,
            fecha=evento_datos['fecha'],
            titulo=evento_datos['titulo'],
            descripcion=evento_datos['descripcion'],
            orden=evento_datos.get('orden', 0)
        )

def crear_conceptos_desde_json(esquema, datos_json):
    """
    Crea conceptos en la base de datos desde JSON para mapas conceptuales
    """
    from .models import ConceptoMapa
    
    # Crear concepto central
    ConceptoMapa.objects.create(
        esquema=esquema,
        texto=datos_json['concepto_central'],
        es_central=True,
        descripcion="Concepto central del mapa"
    )
    
    # Crear conceptos relacionados
    for concepto_datos in datos_json.get('conceptos', []):
        ConceptoMapa.objects.create(
            esquema=esquema,
            texto=concepto_datos['texto'],
            descripcion=concepto_datos.get('descripcion', ''),
            es_central=concepto_datos.get('es_central', False)
        )