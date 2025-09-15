# cuestionarios/views.py - VERSION SIN LOGIN (para pruebas)
from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required  # Comentado temporalmente
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import openai
import PyPDF2
import docx
from io import BytesIO
from .models import Cuestionario, Pregunta, RespuestaUsuario, ResultadoCuestionario
from .utils import generar_preguntas_openai, extraer_texto_archivo

# Configurar OpenAI
openai.api_key = settings.OPENAI_API_KEY

# @login_required  # Comentado temporalmente
def cuestionarios_home(request):
    """Vista principal de cuestionarios"""
    return render(request, 'cuestionarios/cuestionarios_home.html', {
        'show_config': False,
        'show_quiz': False,
        'show_results': False
    })

# @login_required  # Comentado temporalmente
def config_cuestionario(request):
    """Vista de configuración según el método seleccionado"""
    method = request.GET.get('method', 'text')
    
    context = {
        'show_config': True,
        'show_quiz': False,
        'show_results': False,
        'method': method
    }
    
    return render(request, 'cuestionarios/cuestionarios_home.html', context)

# @login_required  # Comentado temporalmente
def crear_cuestionario(request):
    """Crear cuestionario desde archivo o texto"""
    if request.method != 'POST':
        return redirect('cuestionarios:home')
    
    try:
        # Obtener datos del formulario
        num_preguntas = int(request.POST.get('num_questions', 10))
        dificultad = request.POST.get('difficulty', 'medio')
        
        # Extraer contenido según el método
        if 'file' in request.FILES:
            # Método archivo
            archivo = request.FILES['file']
            contenido = extraer_texto_archivo(archivo)
            titulo = f"Cuestionario - {archivo.name}"
        else:
            # Método texto
            contenido = request.POST.get('text_content', '')
            titulo = f"Cuestionario - {contenido[:50]}..."
        
        if not contenido.strip():
            messages.error(request, 'No se pudo extraer contenido válido.')
            return redirect('cuestionarios:home')
        
        # Crear el cuestionario en la base de datos
        # Para pruebas sin usuario, usa un usuario ficticio o None
        cuestionario = Cuestionario.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            titulo=titulo,
            contenido_original=contenido,
            num_preguntas=num_preguntas,
            dificultad=dificultad
        )
        
        # Generar preguntas con OpenAI
        preguntas_data = generar_preguntas_openai(contenido, num_preguntas, dificultad)
        
        # Guardar preguntas en la base de datos
        for i, pregunta_data in enumerate(preguntas_data, 1):
            Pregunta.objects.create(
                cuestionario=cuestionario,
                numero=i,
                texto=pregunta_data['pregunta'],
                opciones=pregunta_data['opciones'],
                respuesta_correcta=pregunta_data['respuesta_correcta']
            )
        
        # Redirigir al quiz
        return redirect('cuestionarios:quiz', quiz_id=cuestionario.id)
        
    except Exception as e:
        messages.error(request, f'Error al crear el cuestionario: {str(e)}')
        return redirect('cuestionarios:home')

# @login_required  # Comentado temporalmente
def mostrar_quiz(request, quiz_id):
    """Mostrar pregunta actual del quiz"""
    cuestionario = get_object_or_404(Cuestionario, id=quiz_id)
    
    # Obtener pregunta actual (primera sin responder)
    pregunta_actual = cuestionario.preguntas.filter(
        respuestausuario__isnull=True
    ).first()
    
    if not pregunta_actual:
        # No hay más preguntas, mostrar resultados
        return redirect('cuestionarios:results', quiz_id=quiz_id)
    
    # Calcular progreso
    preguntas_respondidas = RespuestaUsuario.objects.filter(cuestionario=cuestionario).count()
    total_preguntas = cuestionario.preguntas.count()
    progress_percentage = (preguntas_respondidas / total_preguntas) * 100 if total_preguntas > 0 else 0
    
    context = {
        'show_config': False,
        'show_quiz': True,
        'show_results': False,
        'quiz_id': quiz_id,
        'current_question': preguntas_respondidas + 1,
        'total_questions': total_preguntas,
        'progress_percentage': progress_percentage,
        'question_text': pregunta_actual.texto,
        'answers': pregunta_actual.opciones
    }
    
    return render(request, 'cuestionarios/cuestionarios_home.html', context)

# @login_required  # Comentado temporalmente
def responder_pregunta(request):
    """Procesar respuesta de una pregunta"""
    if request.method != 'POST':
        return redirect('cuestionarios:home')
    
    quiz_id = request.POST.get('quiz_id')
    question_num = int(request.POST.get('question_num'))
    action = request.POST.get('action')
    respuesta = request.POST.get('answer')
    
    cuestionario = get_object_or_404(Cuestionario, id=quiz_id)
    pregunta = get_object_or_404(Pregunta, cuestionario=cuestionario, numero=question_num)
    
    # Procesar respuesta
    if action == 'next' and respuesta is not None:
        respuesta_idx = int(respuesta)
        es_correcta = respuesta_idx == pregunta.respuesta_correcta
        
        # Guardar respuesta
        RespuestaUsuario.objects.update_or_create(
            cuestionario=cuestionario,
            pregunta=pregunta,
            defaults={
                'respuesta_seleccionada': respuesta_idx,
                'es_correcta': es_correcta
            }
        )
    elif action == 'skip':
        # Marcar como saltada (sin respuesta)
        RespuestaUsuario.objects.update_or_create(
            cuestionario=cuestionario,
            pregunta=pregunta,
            defaults={
                'respuesta_seleccionada': None,
                'es_correcta': False
            }
        )
    
    # Verificar si quedan más preguntas
    preguntas_restantes = cuestionario.preguntas.filter(
        respuestausuario__isnull=True
    ).exists()
    
    if preguntas_restantes:
        return redirect('cuestionarios:quiz', quiz_id=quiz_id)
    else:
        # Marcar cuestionario como completado y calcular resultados
        cuestionario.completado = True
        cuestionario.save()
        calcular_resultados(cuestionario)
        return redirect('cuestionarios:results', quiz_id=quiz_id)

# @login_required  # Comentado temporalmente
def mostrar_resultados(request, quiz_id):
    """Mostrar resultados del cuestionario"""
    cuestionario = get_object_or_404(Cuestionario, id=quiz_id)
    
    # Obtener o crear resultado
    resultado, created = ResultadoCuestionario.objects.get_or_create(
        cuestionario=cuestionario,
        defaults={
            'puntuacion': 0,
            'respuestas_correctas': 0,
            'respuestas_incorrectas': 0,
            'total_preguntas': 0
        }
    )
    
    if created:
        calcular_resultados(cuestionario)
        resultado.refresh_from_db()
    
    context = {
        'show_config': False,
        'show_quiz': False,
        'show_results': True,
        'quiz_id': quiz_id,
        'score': int(resultado.puntuacion),
        'correct_answers': resultado.respuestas_correctas,
        'incorrect_answers': resultado.respuestas_incorrectas,
        'total_questions': resultado.total_preguntas,
        'show_review': False
    }
    
    return render(request, 'cuestionarios/cuestionarios_home.html', context)

# @login_required  # Comentado temporalmente
def revisar_respuestas(request):
    """Mostrar revisión detallada de respuestas"""
    if request.method != 'POST':
        return redirect('cuestionarios:home')
    
    quiz_id = request.POST.get('quiz_id')
    cuestionario = get_object_or_404(Cuestionario, id=quiz_id)
    resultado = get_object_or_404(ResultadoCuestionario, cuestionario=cuestionario)
    
    # Preparar datos de revisión
    review_data = []
    for pregunta in cuestionario.preguntas.all():
        try:
            respuesta_usuario = RespuestaUsuario.objects.get(
                cuestionario=cuestionario,
                pregunta=pregunta
            )
            
            user_answer = None
            if respuesta_usuario.respuesta_seleccionada is not None:
                user_answer = pregunta.opciones[respuesta_usuario.respuesta_seleccionada]
            
            review_data.append({
                'question': pregunta.texto,
                'user_answer': user_answer,
                'correct_answer': pregunta.opciones[pregunta.respuesta_correcta],
                'correct': respuesta_usuario.es_correcta
            })
        except RespuestaUsuario.DoesNotExist:
            review_data.append({
                'question': pregunta.texto,
                'user_answer': None,
                'correct_answer': pregunta.opciones[pregunta.respuesta_correcta],
                'correct': False
            })
    
    context = {
        'show_config': False,
        'show_quiz': False,
        'show_results': True,
        'quiz_id': quiz_id,
        'score': int(resultado.puntuacion),
        'correct_answers': resultado.respuestas_correctas,
        'incorrect_answers': resultado.respuestas_incorrectas,
        'total_questions': resultado.total_preguntas,
        'show_review': True,
        'review_data': review_data
    }
    
    return render(request, 'cuestionarios/cuestionarios_home.html', context)

def calcular_resultados(cuestionario):
    """Calcular y guardar resultados del cuestionario"""
    respuestas = RespuestaUsuario.objects.filter(cuestionario=cuestionario)
    total_preguntas = respuestas.count()
    respuestas_correctas = respuestas.filter(es_correcta=True).count()
    respuestas_incorrectas = total_preguntas - respuestas_correctas
    
    puntuacion = (respuestas_correctas / total_preguntas * 100) if total_preguntas > 0 else 0
    
    # Actualizar o crear resultado
    ResultadoCuestionario.objects.update_or_create(
        cuestionario=cuestionario,
        defaults={
            'puntuacion': puntuacion,
            'respuestas_correctas': respuestas_correctas,
            'respuestas_incorrectas': respuestas_incorrectas,
            'total_preguntas': total_preguntas
        }
    )