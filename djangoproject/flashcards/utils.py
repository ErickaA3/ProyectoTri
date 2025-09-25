import json
import openai
import PyPDF2
import docx
from django.conf import settings

# Configurar OpenAI
openai.api_key = settings.OPENAI_API_KEY

def extract_text_from_file(file):
    """
    Extrae texto de diferentes tipos de archivo
    
    Args:
        file: Archivo subido por el usuario
        
    Returns:
        str: Texto extraído del archivo
        
    Raises:
        Exception: Si hay error al procesar el archivo
    """
    text = ""
    file_extension = file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                
        elif file_extension == 'txt':
            text = file.read().decode('utf-8')
            
        elif file_extension in ['doc', 'docx']:
            doc = docx.Document(file)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        else:
            raise Exception(f"Formato de archivo no soportado: {file_extension}")
        
        return text.strip()
        
    except Exception as e:
        raise Exception(f"Error al procesar el archivo {file.name}: {str(e)}")

def get_difficulty_instructions(difficulty):
    """
    Obtiene las instrucciones específicas para cada nivel de dificultad
    
    Args:
        difficulty (str): Nivel de dificultad ('facil', 'intermedio', 'avanzado')
        
    Returns:
        str: Instrucciones específicas para el nivel
    """
    difficulty_map = {
        'facil': 'preguntas básicas de definición, conceptos simples y memorización directa',
        'intermedio': 'preguntas de comprensión, aplicación de conceptos y relaciones entre ideas',
        'avanzado': 'preguntas de análisis crítico, síntesis, evaluación y aplicación compleja'
    }
    return difficulty_map.get(difficulty, difficulty_map['facil'])

def create_flashcards_prompt(text, difficulty, quantity):
    """
    Crea el prompt para OpenAI para generar flashcards
    
    Args:
        text (str): Texto a procesar
        difficulty (str): Nivel de dificultad
        quantity (int): Cantidad de flashcards a generar
        
    Returns:
        str: Prompt completo para OpenAI
    """
    difficulty_instructions = get_difficulty_instructions(difficulty)
    
    prompt = f"""
Analiza el siguiente texto y crea exactamente {quantity} flashcards educativas con {difficulty_instructions}.

INSTRUCCIONES IMPORTANTES:
- Crea preguntas claras y respuestas precisas
- Las preguntas deben ser específicas y directas
- Las respuestas deben ser completas pero concisas
- Varía el tipo de preguntas (definición, explicación, aplicación, etc.)
- Asegúrate de cubrir los conceptos más importantes del texto
- No repitas información en diferentes tarjetas
- Las preguntas deben poder responderse con la información del texto

FORMATO DE RESPUESTA (JSON válido):
[
    {{
        "question": "¿Pregunta específica aquí?",
        "answer": "Respuesta completa y precisa aquí"
    }},
    {{
        "question": "¿Otra pregunta específica?",
        "answer": "Otra respuesta completa"
    }}
]

TEXTO A ANALIZAR:
{text[:4000]}

Responde ÚNICAMENTE con el JSON válido, sin explicaciones adicionales:
"""
    return prompt

def generate_flashcards_with_ai(text, difficulty, quantity):
    """
    Genera flashcards usando OpenAI
    
    Args:
        text (str): Texto a procesar
        difficulty (str): Nivel de dificultad
        quantity (int): Cantidad de flashcards
        
    Returns:
        list: Lista de diccionarios con question y answer
        
    Raises:
        Exception: Si hay error en la generación
    """
    prompt = create_flashcards_prompt(text, difficulty, quantity)
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "Eres un experto en educación que crea flashcards efectivas para el aprendizaje. Responde únicamente con JSON válido."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Limpiar el contenido si viene con markdown
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()
        
        flashcards_data = json.loads(content)
        
        # Validar que sea una lista
        if not isinstance(flashcards_data, list):
            raise ValueError("La respuesta de IA no es una lista válida")
        
        # Validar estructura de cada flashcard
        for i, card in enumerate(flashcards_data):
            if not isinstance(card, dict):
                raise ValueError(f"Flashcard {i+1} no tiene formato válido")
            if 'question' not in card or 'answer' not in card:
                raise ValueError(f"Flashcard {i+1} no tiene pregunta o respuesta")
            if not card['question'].strip() or not card['answer'].strip():
                raise ValueError(f"Flashcard {i+1} tiene pregunta o respuesta vacía")
        
        # Limitar a la cantidad solicitada
        flashcards_data = flashcards_data[:quantity]
        
        return flashcards_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"Error al procesar la respuesta de IA (JSON inválido): {str(e)}")
    except openai.APIError as e:
        raise Exception(f"Error de la API de OpenAI: {str(e)}")
    except Exception as e:
        raise Exception(f"Error al generar flashcards: {str(e)}")

def validate_file(file, max_size_mb=10):
    """
    Valida un archivo subido
    
    Args:
        file: Archivo a validar
        max_size_mb (int): Tamaño máximo en MB
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file:
        return False, "No se recibió ningún archivo"
    
    # Validar tamaño
    max_size_bytes = max_size_mb * 1024 * 1024
    if file.size > max_size_bytes:
        return False, f"El archivo es demasiado grande (máximo {max_size_mb}MB)"
    
    # Validar extensión
    allowed_extensions = ['pdf', 'txt', 'doc', 'docx']
    file_extension = file.name.split('.')[-1].lower()
    if file_extension not in allowed_extensions:
        return False, f"Formato no soportado. Use: {', '.join(allowed_extensions).upper()}"
    
    return True, ""

def validate_text_input(text, title, min_length=100):
    """
    Valida entrada de texto
    
    Args:
        text (str): Texto a validar
        title (str): Título a validar
        min_length (int): Longitud mínima del texto
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "El texto es obligatorio"
    
    if not title or not title.strip():
        return False, "El título es obligatorio"
    
    if len(text.strip()) < min_length:
        return False, f"El texto debe tener al menos {min_length} caracteres"
    
    return True, ""

def validate_flashcard_params(difficulty, quantity):
    """
    Valida parámetros de generación de flashcards
    
    Args:
        difficulty (str): Nivel de dificultad
        quantity: Cantidad solicitada
        
    Returns:
        tuple: (is_valid, error_message)
    """
    valid_difficulties = ['facil', 'intermedio', 'avanzado']
    if difficulty not in valid_difficulties:
        return False, f"Dificultad inválida. Use: {', '.join(valid_difficulties)}"
    
    try:
        quantity = int(quantity)
        if quantity < 5 or quantity > 50:
            return False, "La cantidad debe estar entre 5 y 50 flashcards"
    except (ValueError, TypeError):
        return False, "La cantidad debe ser un número válido"
    
    return True, ""

def clean_filename(filename):
    """
    Limpia un nombre de archivo para usar como título
    
    Args:
        filename (str): Nombre del archivo
        
    Returns:
        str: Nombre limpio sin extensión
    """
    if not filename:
        return "Sin título"
    
    # Remover extensión
    name = filename.rsplit('.', 1)[0]
    
    # Reemplazar caracteres problemáticos
    name = name.replace('_', ' ').replace('-', ' ')
    
    # Capitalizar primera letra
    name = name.strip().capitalize()
    
    return name if name else "Sin título"