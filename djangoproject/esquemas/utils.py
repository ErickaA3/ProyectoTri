# esquemas/utils.py
import os
import json
import PyPDF2
import docx
from openai import OpenAI
from django.conf import settings

def extraer_texto_archivo(archivo):
    """
    Extrae texto de diferentes tipos de archivo
    """
    nombre_archivo = archivo.name.lower()
    
    if nombre_archivo.endswith('.pdf'):
        return extraer_texto_pdf(archivo)
    elif nombre_archivo.endswith(('.doc', '.docx')):
        return extraer_texto_word(archivo)
    elif nombre_archivo.endswith('.txt'):
        return extraer_texto_txt(archivo)
    else:
        raise ValueError("Formato de archivo no soportado")


def extraer_texto_pdf(archivo):
    """Extrae texto de archivos PDF"""
    try:
        reader = PyPDF2.PdfReader(archivo)
        texto = ""
        for pagina in reader.pages:
            texto += pagina.extract_text()
        return texto
    except Exception as e:
        raise ValueError(f"Error al leer PDF: {str(e)}")


def extraer_texto_word(archivo):
    """Extrae texto de archivos Word"""
    try:
        doc = docx.Document(archivo)
        texto = ""
        for parrafo in doc.paragraphs:
            texto += parrafo.text + "\n"
        return texto
    except Exception as e:
        raise ValueError(f"Error al leer documento Word: {str(e)}")


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
    Genera un esquema usando OpenAI GPT
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompts = {
        'jerarquico': """
        Analiza el siguiente texto y crea un esquema jerárquico bien estructurado.
        Devuelve SOLO un JSON válido con esta estructura:
        {
            "titulo": "Título principal del tema",
            "nodos": [
                {
                    "texto": "Punto principal 1",
                    "nivel": 1,
                    "orden": 0,
                    "hijos": [
                        {
                            "texto": "Subpunto 1.1",
                            "nivel": 2,
                            "orden": 0,
                            "hijos": [
                                {
                                    "texto": "Sub-subpunto 1.1.1",
                                    "nivel": 3,
                                    "orden": 0
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        Texto a analizar:
        """,
        
        'conceptual': """
        Analiza el siguiente texto y crea un mapa conceptual.
        Devuelve SOLO un JSON válido con esta estructura:
        {
            "titulo": "Título del mapa conceptual",
            "concepto_central": "Concepto principal",
            "conceptos": [
                {
                    "texto": "Concepto relacionado 1",
                    "descripcion": "Descripción o puntos clave del concepto",
                    "es_central": false
                }
            ]
        }
        
        Texto a analizar:
        """,
        
        'cronologico': """
        Analiza el siguiente texto y crea una línea de tiempo cronológica.
        Devuelve SOLO un JSON válido con esta estructura:
        {
            "titulo": "Título de la línea de tiempo",
            "eventos": [
                {
                    "fecha": "1837",
                    "titulo": "Evento importante",
                    "descripcion": "Descripción del evento",
                    "orden": 0
                }
            ]
        }
        
        Texto a analizar:
        """
    }
    
    try:
        prompt = prompts.get(tipo_esquema, prompts['jerarquico'])
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "Eres un experto en crear esquemas educativos. Responde ÚNICAMENTE con JSON válido, sin texto adicional."
                },
                {
                    "role": "user", 
                    "content": f"{prompt}\n\n{texto}"
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        contenido_respuesta = response.choices[0].message.content.strip()
        
        # Limpiar la respuesta para asegurar que sea JSON válido
        if contenido_respuesta.startswith('```json'):
            contenido_respuesta = contenido_respuesta[7:]
        if contenido_respuesta.endswith('```'):
            contenido_respuesta = contenido_respuesta[:-3]
            
        return json.loads(contenido_respuesta)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al procesar respuesta de OpenAI: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error al conectar con OpenAI: {str(e)}")


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