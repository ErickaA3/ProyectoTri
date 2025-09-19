from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import FlashcardCollection, Flashcard, StudySession
from .utils import (
    extract_text_from_file,
    generate_flashcards_with_ai,
    validate_file,
    validate_text_input,
    validate_flashcard_params,
    clean_filename
)

def flashcards_home(request):
    """Vista principal de flashcards"""
    return render(request, 'flashcards/flashcards_home.html')

@csrf_exempt
def process_file(request):
    """Procesa archivo y genera flashcards"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        file = request.FILES.get('file')
        title = request.POST.get('title', '').strip()
        difficulty = request.POST.get('difficulty', 'facil')
        quantity = request.POST.get('quantity', 20)
        
        # Validar archivo
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            return JsonResponse({'success': False, 'error': error_msg})
        
        # Validar parámetros de flashcards
        is_valid, error_msg = validate_flashcard_params(difficulty, quantity)
        if not is_valid:
            return JsonResponse({'success': False, 'error': error_msg})
        
        quantity = int(quantity)
        
        # Generar título si no se proporcionó
        if not title:
            title = clean_filename(file.name)
        
        # Extraer texto del archivo
        try:
            text = extract_text_from_file(file)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
        if not text or len(text.strip()) < 100:
            return JsonResponse({
                'success': False, 
                'error': 'El archivo no contiene suficiente texto para generar flashcards'
            })
        
        # Generar flashcards con IA
        try:
            flashcards_data = generate_flashcards_with_ai(text, difficulty, quantity)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
        if not flashcards_data:
            return JsonResponse({
                'success': False, 
                'error': 'No se pudieron generar flashcards'
            })
        
        # Crear colección en la base de datos
        collection = FlashcardCollection.objects.create(
            title=title,
            difficulty=difficulty
        )
        
        # Crear flashcards
        for i, card_data in enumerate(flashcards_data):
            Flashcard.objects.create(
                collection=collection,
                question=card_data.get('question', ''),
                answer=card_data.get('answer', ''),
                order=i + 1
            )
        
        # Actualizar contador
        collection.total_cards = len(flashcards_data)
        collection.save()
        
        return JsonResponse({
            'success': True,
            'collection_id': str(collection.id),
            'total_cards': collection.total_cards
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error interno del servidor: {str(e)}'
        })

@csrf_exempt
def process_text(request):
    """Procesa texto directo y genera flashcards"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        title = data.get('title', '').strip()
        difficulty = data.get('difficulty', 'facil')
        quantity = data.get('quantity', 20)
        
        # Validar entrada de texto
        is_valid, error_msg = validate_text_input(text, title)
        if not is_valid:
            return JsonResponse({'success': False, 'error': error_msg})
        
        # Validar parámetros de flashcards
        is_valid, error_msg = validate_flashcard_params(difficulty, quantity)
        if not is_valid:
            return JsonResponse({'success': False, 'error': error_msg})
        
        quantity = int(quantity)
        
        # Generar flashcards con IA
        try:
            flashcards_data = generate_flashcards_with_ai(text, difficulty, quantity)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
        if not flashcards_data:
            return JsonResponse({
                'success': False, 
                'error': 'No se pudieron generar flashcards'
            })
        
        # Crear colección en la base de datos
        collection = FlashcardCollection.objects.create(
            title=title,
            difficulty=difficulty
        )
        
        # Crear flashcards
        for i, card_data in enumerate(flashcards_data):
            Flashcard.objects.create(
                collection=collection,
                question=card_data.get('question', ''),
                answer=card_data.get('answer', ''),
                order=i + 1
            )
        
        # Actualizar contador
        collection.total_cards = len(flashcards_data)
        collection.save()
        
        return JsonResponse({
            'success': True,
            'collection_id': str(collection.id),
            'total_cards': collection.total_cards
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error interno del servidor: {str(e)}'
        })

def view_collection(request, collection_id):
    """Vista para mostrar una colección de flashcards"""
    collection = get_object_or_404(FlashcardCollection, id=collection_id)
    flashcards = collection.flashcards.all()
    
    # Obtener estadísticas de estudio
    study_sessions = StudySession.objects.filter(
        collection=collection,
        completed_at__isnull=False
    ).order_by('-completed_at')
    
    total_sessions = study_sessions.count()
    last_session = study_sessions.first()
    
    # Calcular estadísticas
    avg_accuracy = 0
    if total_sessions > 0:
        total_correct = sum(session.correct_answers for session in study_sessions)
        total_attempted = sum(session.total_cards for session in study_sessions)
        avg_accuracy = round((total_correct / total_attempted) * 100, 1) if total_attempted > 0 else 0
    
    context = {
        'collection': collection,
        'flashcards': flashcards,
        'total_cards': flashcards.count(),
        'total_sessions': total_sessions,
        'last_session': last_session,
        'avg_accuracy': avg_accuracy,
    }
    
    return render(request, 'flashcards/view_collection.html', context)

def my_flashcards(request):
    """Vista para mostrar todas las colecciones"""
    collections = FlashcardCollection.objects.all()
    
    # Agregar estadísticas de progreso para cada colección
    collections_with_stats = []
    for collection in collections:
        # Obtener la última sesión completada
        last_session = StudySession.objects.filter(
            collection=collection,
            completed_at__isnull=False
        ).order_by('-completed_at').first()
        
        # Calcular progreso basado en la última sesión
        if last_session and last_session.total_cards > 0:
            accuracy = last_session.accuracy
            progress_percentage = min(accuracy, 100)  # Cap at 100%
        else:
            accuracy = 0
            progress_percentage = 0
        
        collections_with_stats.append({
            'collection': collection,
            'last_accuracy': accuracy,
            'progress_percentage': progress_percentage,
            'has_been_studied': last_session is not None
        })
    
    context = {
        'collections_with_stats': collections_with_stats,
        'collections': collections,  # Mantener para compatibilidad
        'total_collections': collections.count()
    }
    
    return render(request, 'flashcards/my_flashcards.html', context)

def study_collection(request, collection_id):
    """Vista para estudiar una colección"""
    collection = get_object_or_404(FlashcardCollection, id=collection_id)
    flashcards = list(collection.flashcards.all())
    
    if not flashcards:
        return render(request, 'flashcards/view_collection.html', {
            'collection': collection,
            'flashcards': flashcards,
            'total_cards': 0,
            'error': 'Esta colección no tiene flashcards para estudiar.'
        })
    
    # Crear sesión de estudio
    session = StudySession.objects.create(
        collection=collection,
        total_cards=len(flashcards)
    )
    
    # Serializar flashcards para JavaScript
    flashcards_data = []
    for flashcard in flashcards:
        flashcards_data.append({
            'pk': flashcard.pk,
            'fields': {
                'question': flashcard.question,
                'answer': flashcard.answer,
                'order': flashcard.order
            }
        })
    
    context = {
        'collection': collection,
        'flashcards': json.dumps(flashcards_data),
        'session_id': session.id,
        'total_cards': len(flashcards)
    }
    
    return render(request, 'flashcards/study_collection.html', context)

@csrf_exempt
def complete_study_session(request, session_id):
    """Completa una sesión de estudio"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        correct_answers = int(data.get('correct_answers', 0))
        
        session = get_object_or_404(StudySession, id=session_id)
        
        # Validar que el número de respuestas correctas sea válido
        if correct_answers < 0 or correct_answers > session.total_cards:
            return JsonResponse({
                'success': False, 
                'error': 'Número de respuestas correctas inválido'
            })
        
        session.completed_at = timezone.now()
        session.correct_answers = correct_answers
        session.save()
        
        return JsonResponse({
            'success': True,
            'accuracy': session.accuracy,
            'total_cards': session.total_cards,
            'correct_answers': session.correct_answers
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error al completar sesión: {str(e)}'
        })

@csrf_exempt
def delete_collection(request, collection_id):
    """Elimina una colección de flashcards"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        collection = get_object_or_404(FlashcardCollection, id=collection_id)
        collection_title = collection.title
        
        # Eliminar la colección (esto también eliminará las flashcards y sesiones por CASCADE)
        collection.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Colección "{collection_title}" eliminada correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error al eliminar colección: {str(e)}'
        })