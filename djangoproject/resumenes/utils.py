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

def generate_summary_with_openai(text):
    """Genera un resumen usando OpenAI"""
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": """Eres un asistente especializado en crear resúmenes educativos. 
                    Tu tarea es crear resúmenes claros, organizados y útiles para estudiantes.
                    
                    Formato del resumen:
                    1. Título principal
                    2. Ideas principales (3-5 puntos máximo)
                    3. Conceptos clave
                    4. Conclusión breve
                    
                    Usa un lenguaje claro y académico, pero accesible."""
                },
                {
                    "role": "user", 
                    "content": f"Por favor, crea un resumen estructurado del siguiente texto:\n\n{text}"
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error al generar el resumen: {str(e)}"

def generate_outline_with_openai(text):
    """Genera un esquema usando OpenAI"""
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4",
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
                    "content": f"Crea un esquema detallado del siguiente texto:\n\n{text}"
                }
            ],
            max_tokens=1000,
            temperature=0.5
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error al generar el esquema: {str(e)}"