# cuestionarios/utils.py
import openai
import PyPDF2
import docx
import json
from io import BytesIO
from django.conf import settings

def extraer_texto_archivo(archivo):
    """Extraer texto de diferentes tipos de archivos"""
    contenido = ""
    
    try:
        if archivo.name.endswith('.pdf'):
            contenido = extraer_texto_pdf(archivo)
        elif archivo.name.endswith(('.doc', '.docx')):
            contenido = extraer_texto_word(archivo)
        elif archivo.name.endswith('.txt'):
            contenido = archivo.read().decode('utf-8')
        else:
            raise ValueError("Formato de archivo no soportado")
            
    except Exception as e:
        raise ValueError(f"Error al procesar el archivo: {str(e)}")
    
    return contenido

def extraer_texto_pdf(archivo):
    """Extraer texto de archivo PDF"""
    texto = ""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(archivo.read()))
        for page in pdf_reader.pages:
            texto += page.extract_text() + "\n"
    except Exception as e:
        raise ValueError(f"Error al leer PDF: {str(e)}")
    
    return texto

def extraer_texto_word(archivo):
    """Extraer texto de archivo Word"""
    try:
        doc = docx.Document(BytesIO(archivo.read()))
        texto = ""
        for paragraph in doc.paragraphs:
            texto += paragraph.text + "\n"
    except Exception as e:
        raise ValueError(f"Error al leer documento Word: {str(e)}")
    
    return texto

def generar_preguntas_openai(contenido, num_preguntas, dificultad):
    """Generar preguntas usando OpenAI API"""
    
    # Configurar el prompt según la dificultad
    if dificultad == 'facil':
        prompt_dificultad = "preguntas básicas y directas sobre conceptos principales"
    elif dificultad == 'medio':
        prompt_dificultad = "preguntas de comprensión y análisis de nivel intermedio"
    else:  # dificil
        prompt_dificultad = "preguntas avanzadas que requieren análisis crítico y síntesis"
    
    prompt = f"""
    Basándote en el siguiente contenido, genera exactamente {num_preguntas} preguntas de opción múltiple.
    
    Criterios:
    - Dificultad: {prompt_dificultad}
    - Cada pregunta debe tener exactamente 4 opciones de respuesta (A, B, C, D)
    - Solo una opción debe ser correcta
    - Las opciones incorrectas deben ser plausibles pero claramente incorrectas
    - Las preguntas deben cubrir diferentes aspectos del contenido
    - Evita preguntas ambiguas o con múltiples respuestas correctas
    
    Formato de respuesta (JSON válido):
    [
        {{
            "pregunta": "¿Cuál es...?",
            "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "respuesta_correcta": 0
        }},
        ...
    ]
    
    CONTENIDO:
    {contenido[:4000]}
    
    Responde únicamente con el JSON, sin texto adicional:
    """
    
    try:
        # Usar la nueva API de OpenAI (v1.0+)
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "Eres un experto en crear cuestionarios educativos. Siempre respondes en formato JSON válido."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        # Extraer el contenido de la respuesta
        respuesta_texto = response.choices[0].message.content.strip()
        
        # Limpiar la respuesta por si contiene markdown o texto extra
        if "```json" in respuesta_texto:
            respuesta_texto = respuesta_texto.split("```json")[1].split("```")[0]
        elif "```" in respuesta_texto:
            respuesta_texto = respuesta_texto.split("```")[1]
        
        # Parsear JSON
        preguntas_data = json.loads(respuesta_texto)
        
        # Validar estructura
        if not isinstance(preguntas_data, list):
            raise ValueError("La respuesta no es una lista")
        
        preguntas_validadas = []
        for i, pregunta in enumerate(preguntas_data[:num_preguntas]):
            if not all(key in pregunta for key in ['pregunta', 'opciones', 'respuesta_correcta']):
                raise ValueError(f"Pregunta {i+1} no tiene la estructura correcta")
            
            if len(pregunta['opciones']) != 4:
                raise ValueError(f"Pregunta {i+1} no tiene exactamente 4 opciones")
            
            if not (0 <= pregunta['respuesta_correcta'] <= 3):
                raise ValueError(f"Pregunta {i+1} tiene respuesta_correcta inválida")
            
            preguntas_validadas.append(pregunta)
        
        return preguntas_validadas
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al parsear JSON de OpenAI: {str(e)}")
    except openai.OpenAIError as e:
        raise ValueError(f"Error de OpenAI API: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error inesperado al generar preguntas: {str(e)}")

def generar_preguntas_fallback(contenido, num_preguntas):
    """Generar preguntas básicas como fallback si falla OpenAI"""
    # Esta función se puede usar como respaldo si falla la API de OpenAI
    palabras = contenido.split()
    
    preguntas_fallback = []
    for i in range(min(num_preguntas, 5)):  # Máximo 5 preguntas básicas
        if len(palabras) > 10:
            fragmento = ' '.join(palabras[i*20:(i+1)*20])
            pregunta = {
                "pregunta": f"¿Cuál es el tema principal del siguiente fragmento: '{fragmento[:100]}...'?",
                "opciones": [
                    "Tema relacionado con el contenido",
                    "Tema no relacionado A",
                    "Tema no relacionado B", 
                    "Tema no relacionado C"
                ],
                "respuesta_correcta": 0
            }
            preguntas_fallback.append(pregunta)
    
    return preguntas_fallback