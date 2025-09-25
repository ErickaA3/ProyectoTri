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


def truncar_texto_para_openai(texto, max_tokens=3000):
    """
    Trunca el texto para que quepa dentro del límite de tokens de OpenAI
    Estima ~4 caracteres por token en español
    """
    max_chars = max_tokens * 4
    if len(texto) <= max_chars:
        return texto
    
    # Truncar manteniendo párrafos completos cuando sea posible
    truncated = texto[:max_chars]
    last_paragraph = truncated.rfind('\n\n')
    
    if last_paragraph > max_chars * 0.7:  # Si tenemos al menos 70% del texto
        return truncated[:last_paragraph] + "\n\n[...texto truncado...]"
    else:
        return truncated + "\n\n[...texto truncado...]"


def generar_esquema_openai(texto, tipo_esquema):
    """
    Genera un esquema usando OpenAI GPT con información expandible
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Truncar el texto de entrada para evitar exceder límites
    texto_truncado = truncar_texto_para_openai(texto, max_tokens=3000)
    
    prompts = {
        'jerarquico': """
Analiza el siguiente texto y crea un esquema jerárquico muy detallado con información expandible rica.
Devuelve SOLO un JSON válido con esta estructura exacta:
{
    "titulo": "Título principal del tema",
    "nodos": [
        {
            "texto": "Punto principal 1",
            "nivel": 1,
            "orden": 0,
            "detalles": "Información detallada expandible de al menos 2-3 oraciones que explique este punto en profundidad, incluyendo contexto, importancia, relaciones con otros conceptos, ejemplos específicos o aplicaciones prácticas. Debe ser información valiosa que complemente el título principal.",
            "palabras_clave": ["palabra1", "palabra2", "palabra3", "palabra4"],
            "hijos": [
                {
                    "texto": "Subpunto 1.1",
                    "nivel": 2,
                    "orden": 0,
                    "detalles": "Explicación específica de este subpunto con detalles técnicos, metodologías, características particulares, beneficios, limitaciones o ejemplos concretos. Debe proporcionar información que ayude a entender mejor este aspecto específico.",
                    "palabras_clave": ["concepto", "ejemplo", "método"],
                    "hijos": [
                        {
                            "texto": "Sub-subpunto 1.1.1",
                            "nivel": 3,
                            "orden": 0,
                            "detalles": "Información muy específica sobre este punto particular, incluyendo datos precisos, casos de uso, procedimientos detallados, o análisis profundo del tema.",
                            "palabras_clave": ["detalle", "específico"]
                        }
                    ]
                }
            ]
        }
    ]
}

IMPORTANTE: 
- CADA nodo DEBE tener detalles extensos y específicos (mínimo 100 caracteres por detalle)
- Los detalles deben ser informativos, específicos y valiosos, no repetir el título
- Las palabras_clave deben ser conceptos relevantes y específicos (3-5 palabras por nodo)
- Los detalles deben incluir: contexto, ejemplos, aplicaciones, características, beneficios, etc.
- Máximo 3 niveles de profundidad
- Prioriza calidad y especificidad sobre cantidad

Texto a analizar:
""",
        
        'conceptual': """
Analiza el siguiente texto y crea un mapa conceptual detallado.
Devuelve SOLO un JSON válido con esta estructura:
{
    "titulo": "Título del mapa conceptual",
    "concepto_central": "Concepto principal extraído del texto",
    "conceptos": [
        {
            "texto": "Concepto relacionado 1",
            "descripcion": "Descripción detallada del concepto",
            "es_central": false,
            "conexiones": ["concepto2", "concepto3"],
            "importancia": "alta",
            "ejemplos": ["ejemplo1", "ejemplo2"]
        }
    ]
}

Texto a analizar:
""",
        
        'cronologico': """
Analiza el siguiente texto y crea una línea de tiempo detallada.
Devuelve SOLO un JSON válido con esta estructura:
{
    "titulo": "Título de la línea de tiempo",
    "eventos": [
        {
            "fecha": "Año o fecha del evento",
            "titulo": "Nombre del evento",
            "descripcion": "Descripción detallada del evento",
            "orden": 0,
            "importancia": "alta",
            "consecuencias": ["consecuencia1", "consecuencia2"],
            "contexto": "Contexto histórico o situacional"
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
                    "content": "Eres un experto en crear esquemas educativos detallados. Incluye siempre información adicional expandible. Responde ÚNICAMENTE con JSON válido."
                },
                {
                    "role": "user", 
                    "content": f"{prompt}\n\n{texto_truncado}"
                }
            ],
            max_tokens=3000,
            temperature=0.7
        )
        
        contenido_respuesta = response.choices[0].message.content.strip()
        
        # Limpiar la respuesta para asegurar que sea JSON válido
        if contenido_respuesta.startswith('```json'):
            contenido_respuesta = contenido_respuesta[7:]
        if contenido_respuesta.startswith('```'):
            contenido_respuesta = contenido_respuesta[3:]
        if contenido_respuesta.endswith('```'):
            contenido_respuesta = contenido_respuesta[:-3]
            
        # Intentar parsear como JSON
        datos_esquema = json.loads(contenido_respuesta)
        
        # Validar que tiene la estructura mínima necesaria
        if tipo_esquema == 'jerarquico' and 'nodos' not in datos_esquema:
            raise ValueError("El esquema jerárquico no tiene la estructura correcta")
        elif tipo_esquema == 'conceptual' and 'concepto_central' not in datos_esquema:
            raise ValueError("El mapa conceptual no tiene la estructura correcta")
        elif tipo_esquema == 'cronologico' and 'eventos' not in datos_esquema:
            raise ValueError("La línea de tiempo no tiene la estructura correcta")
            
        return datos_esquema
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al procesar respuesta de OpenAI como JSON: {str(e)}")
    except Exception as e:
        # Si es error de límite de tokens, intentar con texto más corto
        if "context_length_exceeded" in str(e) or "maximum context length" in str(e):
            texto_muy_corto = truncar_texto_para_openai(texto, max_tokens=2000)
            return generar_esquema_openai_fallback(texto_muy_corto, tipo_esquema, client)
        
        raise ValueError(f"Error al conectar con OpenAI: {str(e)}")


def generar_esquema_openai_fallback(texto, tipo_esquema, client):
    """
    Función de respaldo con prompts más cortos y límites más estrictos
    """
    prompts_cortos = {
        'jerarquico': "Crea un esquema jerárquico en JSON con nodos, niveles y jerarquía del siguiente texto:",
        'conceptual': "Crea un mapa conceptual en JSON con concepto_central y conceptos relacionados del siguiente texto:",
        'cronologico': "Crea una línea de tiempo en JSON con eventos cronológicos del siguiente texto:"
    }
    
    try:
        prompt = prompts_cortos.get(tipo_esquema, prompts_cortos['jerarquico'])
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[
                {
                    "role": "user", 
                    "content": f"{prompt}\n\n{texto}"
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        contenido_respuesta = response.choices[0].message.content.strip()
        
        # Limpiar JSON
        if contenido_respuesta.startswith('```json'):
            contenido_respuesta = contenido_respuesta[7:]
        if contenido_respuesta.startswith('```'):
            contenido_respuesta = contenido_respuesta[3:]
        if contenido_respuesta.endswith('```'):
            contenido_respuesta = contenido_respuesta[:-3]
        
        return json.loads(contenido_respuesta)
        
    except Exception as e:
        # Si todo falla, crear esquema básico
        return crear_esquema_basico(texto, tipo_esquema)


def crear_esquema_basico(texto, tipo_esquema):
    """
    Crea un esquema básico más detallado cuando OpenAI falla
    """
    titulo = "Esquema generado automáticamente"
    
    # Crear detalles más ricos basados en el texto original
    texto_resumen = texto[:300] if len(texto) > 300 else texto
    
    if tipo_esquema == 'jerarquico':
        return {
            "titulo": titulo,
            "nodos": [
                {
                    "texto": "Tema Principal del Contenido",
                    "nivel": 1,
                    "orden": 0,
                    "detalles": f"Este es el tema central extraído del contenido proporcionado. El texto analizado aborda diversos aspectos y conceptos relacionados con este tema principal. La información incluye múltiples perspectivas y enfoques que se desarrollan a lo largo del contenido, proporcionando una visión integral del tema tratado.",
                    "palabras_clave": ["tema central", "contenido principal", "análisis", "conceptos", "información"],
                    "hijos": [
                        {
                            "texto": "Aspectos Específicos del Contenido",
                            "nivel": 2,
                            "orden": 0,
                            "detalles": f"Esta sección desarrolla los aspectos más relevantes identificados en el texto original. Incluye detalles específicos, ejemplos concretos y explicaciones detalladas que complementan el tema principal. El contenido original menciona: {texto_resumen}...",
                            "palabras_clave": ["aspectos específicos", "detalles", "ejemplos", "desarrollo"]
                        },
                        {
                            "texto": "Información Complementaria",
                            "nivel": 2,
                            "orden": 1,
                            "detalles": "Información adicional que enriquece la comprensión del tema principal. Esta sección incluye contexto adicional, relaciones entre conceptos, y perspectivas que ayudan a tener una visión más completa del contenido analizado.",
                            "palabras_clave": ["información adicional", "contexto", "relaciones", "perspectivas"]
                        }
                    ]
                }
            ]
        }
    elif tipo_esquema == 'conceptual':
        return {
            "titulo": titulo,
            "concepto_central": "Tema Principal",
            "conceptos": [
                {
                    "texto": "Concepto Clave 1",
                    "descripcion": f"Concepto fundamental extraído del contenido analizado. Este concepto representa una idea central que se desarrolla a lo largo del texto y que es esencial para la comprensión del tema. El texto original proporciona evidencia y ejemplos que respaldan este concepto.",
                    "es_central": False,
                    "importancia": "alta",
                    "ejemplos": ["ejemplo del texto", "aplicación práctica", "caso específico"],
                    "conexiones": ["Concepto Clave 2", "Tema Principal"]
                },
                {
                    "texto": "Concepto Clave 2", 
                    "descripcion": "Segundo concepto importante identificado en el análisis del contenido. Este concepto complementa y se relaciona con otros elementos del texto, formando parte de una red conceptual más amplia que facilita la comprensión integral del tema.",
                    "es_central": False,
                    "importancia": "media",
                    "ejemplos": ["ejemplo relacionado", "aplicación específica"],
                    "conexiones": ["Concepto Clave 1"]
                }
            ]
        }
    elif tipo_esquema == 'cronologico':
        return {
            "titulo": titulo,
            "eventos": [
                {
                    "fecha": "Periodo inicial",
                    "titulo": "Evento o Proceso Principal",
                    "descripcion": f"Evento o proceso principal identificado en el contenido analizado. Este elemento temporal representa un momento o desarrollo significativo dentro del contexto del texto. La información incluye detalles sobre causas, desarrollo y efectos del evento descrito.",
                    "orden": 0,
                    "importancia": "alta",
                    "contexto": f"El contexto de este evento se basa en la información proporcionada en el texto original, que incluye circunstancias, antecedentes y factores relevantes para la comprensión completa del proceso.",
                    "consecuencias": ["efecto directo", "impacto a largo plazo", "cambios resultantes"]
                }
            ]
        }


def crear_nodos_desde_json(esquema, datos_json):
    """
    Crea nodos en la base de datos desde JSON para esquemas jerárquicos
    Versión mejorada con información expandible
    """
    from .models import NodoEsquema
    
    # Limpiar nodos existentes para evitar duplicados
    NodoEsquema.objects.filter(esquema=esquema).delete()
    
    def crear_nodo_recursivo(datos_nodo, padre=None, orden_en_nivel=0):
        """Función recursiva que crea nodos manteniendo la jerarquía"""
        
        # Extraer información adicional
        detalles = datos_nodo.get('detalles', '')
        palabras_clave = datos_nodo.get('palabras_clave', [])
        importancia = datos_nodo.get('importancia', 'media')
        
        nodo = NodoEsquema.objects.create(
            esquema=esquema,
            texto=datos_nodo.get('texto', 'Sin texto'),
            nivel=datos_nodo.get('nivel', 1),
            orden=orden_en_nivel,
            padre=padre,
            detalles=detalles,
            palabras_clave=palabras_clave,
            importancia=importancia
        )
        
        # Crear nodos hijos si existen
        if 'hijos' in datos_nodo and datos_nodo['hijos']:
            for i, hijo_datos in enumerate(datos_nodo['hijos']):
                crear_nodo_recursivo(hijo_datos, nodo, i)
        
        return nodo
    
    try:
        # Verificar que el JSON tiene la estructura correcta
        nodos_data = datos_json.get('nodos', [])
        
        if not nodos_data:
            # Si no hay estructura 'nodos', intentar crear desde el JSON completo
            if 'titulo' in datos_json:
                # Crear un nodo raíz con el título
                nodo_raiz = NodoEsquema.objects.create(
                    esquema=esquema,
                    texto=datos_json.get('titulo', esquema.titulo),
                    nivel=1,
                    orden=0,
                    padre=None,
                    detalles="Nodo principal del esquema",
                    palabras_clave=["principal"],
                    importancia="alta"
                )
                return
        
        # Crear todos los nodos principales desde el JSON
        for i, nodo_datos in enumerate(nodos_data):
            crear_nodo_recursivo(nodo_datos, None, i)
            
    except Exception as e:
        # Si hay error, al menos crear un nodo básico para que no esté vacío
        print(f"Error creando nodos desde JSON: {e}")
        if not NodoEsquema.objects.filter(esquema=esquema).exists():
            NodoEsquema.objects.create(
                esquema=esquema,
                texto=f"Error al procesar esquema: {str(e)}",
                nivel=1,
                orden=0,
                padre=None,
                detalles="Se produjo un error durante el procesamiento",
                palabras_clave=["error"],
                importancia="baja"
            )


def crear_eventos_desde_json(esquema, datos_json):
    """
    Crea eventos en la base de datos desde JSON para líneas de tiempo
    Versión mejorada con información expandible
    """
    from .models import EventoTimeline
    
    # Limpiar eventos existentes
    EventoTimeline.objects.filter(esquema=esquema).delete()
    
    try:
        eventos_data = datos_json.get('eventos', [])
        
        for i, evento_datos in enumerate(eventos_data):
            EventoTimeline.objects.create(
                esquema=esquema,
                fecha=evento_datos.get('fecha', 'Fecha no especificada'),
                titulo=evento_datos.get('titulo', 'Evento sin título'),
                descripcion=evento_datos.get('descripcion', 'Sin descripción'),
                orden=evento_datos.get('orden', i),
                importancia=evento_datos.get('importancia', 'media'),
                contexto=evento_datos.get('contexto', ''),
                consecuencias=evento_datos.get('consecuencias', [])
            )
            
    except Exception as e:
        print(f"Error creando eventos desde JSON: {e}")
        # Crear un evento por defecto
        EventoTimeline.objects.create(
            esquema=esquema,
            fecha='Error',
            titulo='Error al procesar línea de tiempo',
            descripcion=str(e),
            orden=0,
            importancia='baja',
            contexto='Error durante el procesamiento'
        )


def crear_conceptos_desde_json(esquema, datos_json):
    """
    Crea conceptos en la base de datos desde JSON para mapas conceptuales
    Versión mejorada con información expandible
    """
    from .models import ConceptoMapa
    
    # Limpiar conceptos existentes
    ConceptoMapa.objects.filter(esquema=esquema).delete()
    
    try:
        # Crear concepto central
        concepto_central_texto = datos_json.get('concepto_central', 'Concepto Principal')
        ConceptoMapa.objects.create(
            esquema=esquema,
            texto=concepto_central_texto,
            es_central=True,
            descripcion="Concepto central del mapa",
            importancia='alta',
            conexiones=[],
            ejemplos=[]
        )
        
        # Crear conceptos relacionados
        conceptos_data = datos_json.get('conceptos', [])
        for concepto_datos in conceptos_data:
            ConceptoMapa.objects.create(
                esquema=esquema,
                texto=concepto_datos.get('texto', 'Concepto sin nombre'),
                descripcion=concepto_datos.get('descripcion', ''),
                es_central=concepto_datos.get('es_central', False),
                importancia=concepto_datos.get('importancia', 'media'),
                conexiones=concepto_datos.get('conexiones', []),
                ejemplos=concepto_datos.get('ejemplos', [])
            )
            
    except Exception as e:
        print(f"Error creando conceptos desde JSON: {e}")
        # Crear conceptos por defecto
        ConceptoMapa.objects.create(
            esquema=esquema,
            texto='Error al procesar mapa conceptual',
            es_central=True,
            descripcion=str(e),
            importancia='baja'
        )


def debug_esquema_jerarquico(esquema):
    """
    Función de debug para esquemas jerárquicos
    Útil para identificar problemas en la estructura
    """
    from .models import NodoEsquema
    
    debug_info = {
        'esquema_id': esquema.id,
        'titulo': esquema.titulo,
        'tipo': esquema.tipo,
        'nodos_en_bd': NodoEsquema.objects.filter(esquema=esquema).count(),
        'json_original': esquema.contenido_procesado,
        'estructura_nodos': []
    }
    
    # Analizar estructura de nodos
    nodos = NodoEsquema.objects.filter(esquema=esquema).order_by('nivel', 'orden')
    for nodo in nodos:
        debug_info['estructura_nodos'].append({
            'id': nodo.id,
            'texto': nodo.texto[:50] + '...' if len(nodo.texto) > 50 else nodo.texto,
            'nivel': nodo.nivel,
            'orden': nodo.orden,
            'padre_id': nodo.padre.id if nodo.padre else None,
            'hijos_count': nodo.hijos.count(),
            'tiene_detalles': nodo.tiene_detalles(),
            'palabras_clave': nodo.get_palabras_clave_str()
        })
    
    return debug_info


def regenerar_nodos_esquema(esquema):
    """
    Regenera los nodos de un esquema desde su JSON almacenado
    Útil para corregir problemas de estructura
    """
    if esquema.tipo != 'jerarquico':
        return False
        
    if not esquema.contenido_procesado:
        return False
    
    try:
        crear_nodos_desde_json(esquema, esquema.contenido_procesado)
        return True
    except Exception as e:
        print(f"Error regenerando nodos: {e}")
        return False


def validar_estructura_json(datos_json, tipo_esquema):
    """
    Valida que el JSON tenga la estructura correcta según el tipo de esquema
    """
    try:
        if tipo_esquema == 'jerarquico':
            if 'nodos' not in datos_json:
                return False, "Falta la clave 'nodos'"
            
            for nodo in datos_json['nodos']:
                if 'texto' not in nodo or 'nivel' not in nodo:
                    return False, "Nodos deben tener 'texto' y 'nivel'"
                    
        elif tipo_esquema == 'conceptual':
            if 'concepto_central' not in datos_json:
                return False, "Falta 'concepto_central'"
            if 'conceptos' not in datos_json:
                return False, "Falta la clave 'conceptos'"
                
        elif tipo_esquema == 'cronologico':
            if 'eventos' not in datos_json:
                return False, "Falta la clave 'eventos'"
            
            for evento in datos_json['eventos']:
                if 'fecha' not in evento or 'titulo' not in evento:
                    return False, "Eventos deben tener 'fecha' y 'titulo'"
        
        return True, "Estructura válida"
        
    except Exception as e:
        return False, f"Error validando JSON: {str(e)}"


def obtener_estadisticas_esquema(esquema):
    """
    Obtiene estadísticas detalladas de un esquema
    """
    from .models import NodoEsquema, EventoTimeline, ConceptoMapa
    
    stats = {
        'id': esquema.id,
        'titulo': esquema.titulo,
        'tipo': esquema.tipo,
        'fecha_creacion': esquema.fecha_creacion,
        'tiene_json': bool(esquema.contenido_procesado),
    }
    
    if esquema.tipo == 'jerarquico':
        nodos = NodoEsquema.objects.filter(esquema=esquema)
        stats.update({
            'total_nodos': nodos.count(),
            'niveles': list(nodos.values_list('nivel', flat=True).distinct().order_by('nivel')),
            'nodos_raiz': nodos.filter(padre=None).count(),
            'nodos_con_hijos': nodos.filter(hijos__isnull=False).distinct().count(),
            'nodos_con_detalles': nodos.exclude(detalles='').count()
        })
        
    elif esquema.tipo == 'conceptual':
        conceptos = ConceptoMapa.objects.filter(esquema=esquema)
        stats.update({
            'total_conceptos': conceptos.count(),
            'conceptos_centrales': conceptos.filter(es_central=True).count(),
            'conceptos_relacionados': conceptos.filter(es_central=False).count()
        })
        
    elif esquema.tipo == 'cronologico':
        eventos = EventoTimeline.objects.filter(esquema=esquema)
        stats.update({
            'total_eventos': eventos.count(),
            'primer_evento': eventos.order_by('orden').first(),
            'ultimo_evento': eventos.order_by('-orden').first()
        })
    
    return stats