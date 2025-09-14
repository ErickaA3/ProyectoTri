from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Document, Summary
from .forms import DocumentForm, TextForm
from .utils import extract_text_from_file, generate_summary_with_openai, generate_outline_with_openai

def home(request):
    """Vista principal con las tarjetas"""
    context = {
        'titulo': 'Procesamiento de Documentos',
        'descripcion': 'Sube archivos o ingresa texto para generar resúmenes automáticos'
    }
    return render(request, 'resumenes/resumenes_home.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def process_file(request):
    """Procesa archivos subidos"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No se encontró archivo'}, status=400)
        
        file = request.FILES['file']
        title = request.POST.get('title', file.name)
        
        # Extraer texto del archivo
        text_content = extract_text_from_file(file)
        
        # Crear documento en la base de datos
        document = Document.objects.create(
            title=title,
            document_type=file.name.split('.')[-1].lower(),
            original_file=file,
            original_text=text_content,
            user=request.user if request.user.is_authenticated else None
        )
        
        # Generar resumen con OpenAI
        summary_text = generate_summary_with_openai(text_content)
        
        # Guardar resumen
        summary = Summary.objects.create(
            document=document,
            summary_text=summary_text
        )
        
        return JsonResponse({
            'success': True,
            'document_id': document.id,
            'summary': summary_text,
            'message': 'Archivo procesado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def process_text(request):
    """Procesa texto ingresado manualmente"""
    try:
        data = json.loads(request.body)
        title = data.get('title', 'Texto sin título')
        text_content = data.get('text', '')
        
        if not text_content.strip():
            return JsonResponse({'error': 'El texto no puede estar vacío'}, status=400)
        
        # Crear documento en la base de datos
        document = Document.objects.create(
            title=title,
            document_type='manual',
            original_text=text_content,
            user=request.user if request.user.is_authenticated else None
        )
        
        # Generar resumen con OpenAI
        summary_text = generate_summary_with_openai(text_content)
        
        # Guardar resumen
        summary = Summary.objects.create(
            document=document,
            summary_text=summary_text
        )
        
        return JsonResponse({
            'success': True,
            'document_id': document.id,
            'summary': summary_text,
            'message': 'Texto procesado exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Error en el formato de datos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def view_summary(request, document_id):
    """Muestra el resumen generado"""
    try:
        document = Document.objects.get(id=document_id)
        summary = Summary.objects.get(document=document)
        
        context = {
            'document': document,
            'summary': summary,
        }
        return render(request, 'resumenes/summary.html', context)
    
    except (Document.DoesNotExist, Summary.DoesNotExist):
        messages.error(request, 'Documento no encontrado')
        return redirect('resumenes:home')
    