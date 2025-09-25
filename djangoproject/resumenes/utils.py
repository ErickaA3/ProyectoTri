import openai
from django.conf import settings
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import io

# Configurar OpenAI
openai.api_key = settings.OPENAI_API_KEY

def extract_text_from_file(file):
    """Extrae texto de diferentes tipos de archivo"""
    file_extension = file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'txt':
            return file.read().decode('utf-8')
        
        elif file_extension == 'pdf':
            pdf_reader = PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        
        elif file_extension in ['doc', 'docx']:
            doc = DocxDocument(file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        
        else:
            raise ValueError(f"Tipo de archivo no soportado: {file_extension}")
    
    except Exception as e:
        raise ValueError(f"Error al procesar el archivo: {str(e)}")

def count_tokens_simple(text):
    """Cuenta tokens de manera simple (aproximación)"""
    # Aproximación: 1 token ≈ 4 caracteres en español
    return len(text) // 4

def truncate_text_for_model(text, max_tokens=6000):
    """Trunca el texto para que quepa en el contexto del modelo"""
    tokens = count_tokens_simple(text)
    
    if tokens <= max_tokens:
        return text
    
    # Calcular aproximadamente cuántos caracteres mantener
    ratio = max_tokens / tokens
    target_length = int(len(text) * ratio * 0.85)  # 85% para margen de seguridad
    
    # Truncar por párrafos para mantener coherencia
    paragraphs = text.split('\n\n')
    truncated_text = ""
    
    for paragraph in paragraphs:
        test_text = truncated_text + paragraph + "\n\n"
        if len(test_text) <= target_length:
            truncated_text = test_text
        else:
            break
    
    # Si no hay párrafos, truncar por caracteres
    if not truncated_text.strip():
        truncated_text = text[:target_length]
    
    return truncated_text.strip()

def generate_summary_with_openai(text):
    """Genera un resumen estructurado usando OpenAI con manejo de límites de tokens"""
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Truncar el texto si es muy largo
        processed_text = truncate_text_for_model(text, max_tokens=5000)
        
        # Agregar nota si el texto fue truncado
        truncated_note = ""
        if len(processed_text) < len(text):
            truncated_note = "\n\n## Nota\n- El texto original era muy largo y se procesó una parte representativa para generar este resumen."
        
        prompt = f"""
        Analiza el siguiente texto y crea un resumen estructurado en formato markdown. 

        IMPORTANTE: Usa EXACTAMENTE este formato con markdown:

        ## Resumen Principal
        [Párrafo breve con la **idea central** del texto]

        ## Puntos Clave
        1. **Primer aspecto importante:** descripción relevante del punto
        2. **Segundo aspecto importante:** descripción relevante del punto  
        3. **Tercer aspecto importante:** descripción relevante del punto
        4. **Cuarto aspecto importante:** descripción relevante del punto

        ## Detalles Importantes
        - **Detalle específico:** explicación del detalle relevante
        - **Otro detalle específico:** explicación del detalle relevante
        - **Detalle adicional:** explicación del detalle importante

        ## Conclusión
        [Párrafo final con las **conclusiones principales** y puntos más **relevantes**]

        REGLAS OBLIGATORIAS:
        - Usa siempre "##" y **negritas** para títulos de sección
        - Para listas ordenadas usa "1. 2. 3." cuando hay secuencia, jerarquía o pasos
        - Para listas simples usa "- " cuando no importa el orden
        - SIEMPRE usa **texto en negrita** para resaltar conceptos clave, términos importantes y palabras relevantes
        - En cada elemento de lista, la primera parte debe estar en **negrita** seguida de dos puntos y luego la explicación
        - Mantén los párrafos claros y concisos
        - Asegúrate de que cada sección tenga contenido útil
        - Resalta con **negritas** nombres propios, fechas importantes, conceptos clave y términos técnicos
        - Elige el formato de lista más apropiado para cada sección

        Texto a resumir:
        {processed_text}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "Eres un experto en crear resúmenes estructurados y claros usando formato markdown. SIEMPRE usas **texto en negrita** para resaltar conceptos importantes, términos clave y palabras relevantes. Sigues el formato exacto solicitado con ## para títulos y - para listas, usando negritas extensivamente para mejorar la legibilidad."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        return summary + truncated_note
    
    except Exception as e:
        # Fallback mejorado con estructura básica
        word_count = len(text.split())
        char_count = len(text)
        
        return f"""## Error en la Generación

No se pudo generar el resumen automático: **{str(e)}**

## Información del Documento

- **Palabras aproximadas:** {word_count:,}
- **Caracteres:** {char_count:,}

## Texto Inicial

{text[:1000]}{'...' if len(text) > 1000 else ''}

## Recomendación

- **Dividir documento:** Intenta dividir el documento en secciones más pequeñas
- **Procesar parcialmente:** O procesa solo la parte más importante del texto"""

def generate_outline_with_openai(text):
    """Genera un esquema usando OpenAI"""
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Truncar texto para esquemas también
        processed_text = truncate_text_for_model(text, max_tokens=4000)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": """Eres un asistente especializado en crear esquemas educativos.
                    Crea esquemas jerárquicos bien organizados usando números y letras.
                    
                    Formato:
                    I. Tema Principal
                        A. Subtema
                            1. Detalle
                            2. Detalle
                        B. Subtema
                    II. Segundo Tema Principal
                    
                    Sé conciso pero completo."""
                },
                {
                    "role": "user", 
                    "content": f"Crea un esquema detallado del siguiente texto:\n\n{processed_text}"
                }
            ],
            max_tokens=600,
            temperature=0.5
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error al generar el esquema: {str(e)}"