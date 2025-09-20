# cuestionarios/views.py - CÓDIGO COMPLETO ACTUALIZADO
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
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

def cuestionarios_home(request):
    """Vista principal de cuestionarios con cuestionarios recientes"""
    
    # Obtener cuestionarios recientes (los últimos 6)
    cuestionarios_recientes = Cuestionario.objects.all().order_by('-fecha_creacion')[:6]
    
    # Debug: imprimir en consola para verificar
    print(f"DEBUG: Cuestionarios encontrados: {cuestionarios_recientes.count()}")
    for c in cuestionarios_recientes:
        print(f"- ID: {c.id}, Título: {c.titulo}, Completado: {c.completado}")
    
    context = {
        'show_config': False,
        'show_quiz': False,
        'show_results': False,
        'cuestionarios_recientes': cuestionarios_recientes
    }
    
    return render(request, 'cuestionarios/cuestionarios_home.html', context)

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

def revisar_respuestas(request):
    """Mostrar revisión detallada de respuestas"""
    if request.method != 'POST':
        return redirect('cuestionarios:home')
    
    quiz_id = request.POST.get('quiz_id')
    cuestionario = get_object_or_404(Cuestionario, id=quiz_id)
    resultado = get_object_or_404(ResultadoCuestionario, cuestionario=cuestionario)
    
    # Preparar datos de revisión con información detallada
    review_data = []
    for pregunta in cuestionario.preguntas.all():
        try:
            respuesta_usuario = RespuestaUsuario.objects.get(
                cuestionario=cuestionario,
                pregunta=pregunta
            )
            
            # Determinar respuesta del usuario
            user_answer = None
            user_answer_text = "No respondida"
            if respuesta_usuario.respuesta_seleccionada is not None:
                user_answer = respuesta_usuario.respuesta_seleccionada
                user_answer_text = pregunta.opciones[respuesta_usuario.respuesta_seleccionada]
            
            # Información completa para la revisión
            review_item = {
                'question': pregunta.texto,
                'question_number': pregunta.numero,
                'user_answer_index': user_answer,
                'user_answer_text': user_answer_text,
                'correct_answer_index': pregunta.respuesta_correcta,
                'correct_answer_text': pregunta.opciones[pregunta.respuesta_correcta],
                'all_options': pregunta.opciones,
                'correct': respuesta_usuario.es_correcta,
                'answered': user_answer is not None
            }
            
            review_data.append(review_item)
            
        except RespuestaUsuario.DoesNotExist:
            # Pregunta no respondida
            review_item = {
                'question': pregunta.texto,
                'question_number': pregunta.numero,
                'user_answer_index': None,
                'user_answer_text': "No respondida",
                'correct_answer_index': pregunta.respuesta_correcta,
                'correct_answer_text': pregunta.opciones[pregunta.respuesta_correcta],
                'all_options': pregunta.opciones,
                'correct': False,
                'answered': False
            }
            
            review_data.append(review_item)
    
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

def ver_cuestionario(request, cuestionario_id):
    """Ver detalles de un cuestionario completado"""
    cuestionario = get_object_or_404(Cuestionario, id=cuestionario_id)
    
    # Verificar si hay resultados
    try:
        resultado = ResultadoCuestionario.objects.get(cuestionario=cuestionario)
    except ResultadoCuestionario.DoesNotExist:
        # Si no hay resultado, redirigir al quiz
        return redirect('cuestionarios:quiz', quiz_id=cuestionario_id)
    
    # Obtener todas las respuestas para mostrar resumen
    respuestas = RespuestaUsuario.objects.filter(cuestionario=cuestionario)
    
    context = {
        'cuestionario': cuestionario,
        'resultado': resultado,
        'respuestas': respuestas,
        'total_preguntas': cuestionario.preguntas.count()
    }
    
    return render(request, 'cuestionarios/ver_cuestionario.html', context)

def eliminar_cuestionario(request, cuestionario_id):
    """Eliminar un cuestionario con confirmación"""
    cuestionario = get_object_or_404(Cuestionario, id=cuestionario_id)
    
    # Verificar permisos (opcional si tienes autenticación)
    if request.user.is_authenticated and cuestionario.usuario != request.user:
        messages.error(request, 'No tienes permisos para eliminar este cuestionario.')
        return redirect('cuestionarios:home')
    
    if request.method == 'POST':
        titulo = cuestionario.titulo
        cuestionario.delete()
        messages.success(request, f'Cuestionario "{titulo}" eliminado correctamente.')
        return redirect('cuestionarios:home')
    
    # Mostrar página de confirmación
    return render(request, 'cuestionarios/confirmar_eliminar.html', {'cuestionario': cuestionario})

def exportar_pdf_cuestionario(request, cuestionario_id):
    """Exportar cuestionario a PDF"""
    cuestionario = get_object_or_404(Cuestionario, id=cuestionario_id)
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        import io
        
        # Crear buffer para el PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []
        
        # Título principal
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
        )
        story.append(Paragraph(cuestionario.titulo, title_style))
        story.append(Spacer(1, 12))
        
        # Metadatos
        story.append(Paragraph(f"<b>Dificultad:</b> {cuestionario.get_dificultad_display()}", styles['Normal']))
        story.append(Paragraph(f"<b>Número de preguntas:</b> {cuestionario.num_preguntas}", styles['Normal']))
        story.append(Paragraph(f"<b>Creado:</b> {cuestionario.fecha_creacion.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        
        # Verificar si hay resultado
        try:
            resultado = ResultadoCuestionario.objects.get(cuestionario=cuestionario)
            story.append(Paragraph(f"<b>Puntuación:</b> {resultado.puntuacion:.0f}%", styles['Normal']))
            story.append(Paragraph(f"<b>Respuestas correctas:</b> {resultado.respuestas_correctas}/{resultado.total_preguntas}", styles['Normal']))
        except ResultadoCuestionario.DoesNotExist:
            story.append(Paragraph("<b>Estado:</b> Cuestionario no completado", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Preguntas y respuestas
        story.append(Paragraph("Preguntas y Respuestas", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        preguntas = cuestionario.preguntas.all().order_by('numero')
        for pregunta in preguntas:
            # Pregunta
            pregunta_style = ParagraphStyle(
                'PreguntaStyle',
                parent=styles['Normal'],
                fontSize=12,
                fontName='Helvetica-Bold',
                spaceAfter=6
            )
            story.append(Paragraph(f"Pregunta {pregunta.numero}: {pregunta.texto}", pregunta_style))
            
            # Opciones
            for i, opcion in enumerate(pregunta.opciones):
                opcion_letra = chr(65 + i)  # A, B, C, D
                es_correcta = i == pregunta.respuesta_correcta
                if es_correcta:
                    opcion_style = ParagraphStyle(
                        'OpcionCorrectaStyle',
                        parent=styles['Normal'],
                        fontSize=10,
                        fontName='Helvetica-Bold'
                    )
                    story.append(Paragraph(f"{opcion_letra}) {opcion} ✓", opcion_style))
                else:
                    story.append(Paragraph(f"{opcion_letra}) {opcion}", styles['Normal']))
            
            # Verificar respuesta del usuario si existe
            try:
                respuesta_usuario = RespuestaUsuario.objects.get(cuestionario=cuestionario, pregunta=pregunta)
                if respuesta_usuario.respuesta_seleccionada is not None:
                    respuesta_letra = chr(65 + respuesta_usuario.respuesta_seleccionada)
                    if respuesta_usuario.es_correcta:
                        story.append(Paragraph(f"<b>Tu respuesta:</b> {respuesta_letra} - Correcta", styles['Normal']))
                    else:
                        story.append(Paragraph(f"<b>Tu respuesta:</b> {respuesta_letra} - Incorrecta", styles['Normal']))
                else:
                    story.append(Paragraph("<b>Tu respuesta:</b> No respondida", styles['Normal']))
            except RespuestaUsuario.DoesNotExist:
                story.append(Paragraph("<b>Tu respuesta:</b> No respondida", styles['Normal']))
            
            story.append(Spacer(1, 12))
        
        # Generar PDF
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Cuestionario_{cuestionario.titulo}.pdf"'
        return response
        
    except ImportError:
        messages.error(request, 'Funcionalidad de PDF no disponible. Instala reportlab.')
        return redirect('cuestionarios:ver_cuestionario', cuestionario_id=cuestionario_id)
    except Exception as e:
        messages.error(request, f'Error al generar PDF: {str(e)}')
        return redirect('cuestionarios:ver_cuestionario', cuestionario_id=cuestionario_id)

def mis_cuestionarios(request):
    """Ver todos los cuestionarios del usuario"""
    cuestionarios = Cuestionario.objects.all().order_by('-fecha_creacion')
    if request.user.is_authenticated:
        cuestionarios = cuestionarios.filter(usuario=request.user)
    
    return render(request, 'cuestionarios/mis_cuestionarios.html', {
        'cuestionarios': cuestionarios
    })

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