from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Document, Summary
from .forms import DocumentForm, TextForm
from .utils import extract_text_from_file, generate_summary_with_openai, generate_outline_with_openai

# IMPORTAR HISTORIAL
try:
    from historial.utils import registrar_actividad
except ImportError:
    # Si no existe el módulo historial, crear una función dummy
    def registrar_actividad(*args, **kwargs):
        pass

def home(request):
    """Vista principal con las tarjetas"""
    try:
        # Obtener los últimos 6 resúmenes recientes
        resumenes_recientes = Document.objects.filter(
            summary__isnull=False  # Solo documentos que tengan resumen
        ).select_related('summary').order_by('-created_at')[:6]
        
        context = {
            'titulo': 'Procesamiento de Documentos',
            'descripcion': 'Sube archivos o ingresa texto para generar resúmenes automáticos',
            'resumenes_recientes': resumenes_recientes,
        }
    except Exception as e:
        # Si hay algún error, mostrar la página sin resúmenes recientes
        context = {
            'titulo': 'Procesamiento de Documentos',
            'descripcion': 'Sube archivos o ingresa texto para generar resúmenes automáticos',
            'resumenes_recientes': [],
        }
    
    return render(request, 'resumenes/resumenes_home.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def process_file(request):
    """Procesa archivos subidos"""
    try:
        if 'file' not in request.FILES:
            messages.error(request, 'No se encontró archivo')
            return redirect('resumenes:home')
        
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
        
        # *** REGISTRAR EN HISTORIAL ***
        registrar_actividad(
            tipo='resumen_creado',
            titulo=title,
            descripcion=f'Desde archivo {file.name.split(".")[-1].upper()} • {len(summary_text.split())} palabras',
            app_origen='resumenes',
            objeto_id=document.id,
            metadata={
                'document_type': document.document_type,
                'archivo_nombre': file.name,
                'palabras_resumen': len(summary_text.split()),
                'palabras_original': len(text_content.split()),
                'fuente': 'archivo'
            }
        )
        
        messages.success(request, 'Archivo procesado exitosamente')
        return redirect('resumenes:view_summary', document_id=document.id)
        
    except Exception as e:
        messages.error(request, f'Error al procesar archivo: {str(e)}')
        return redirect('resumenes:home')

@csrf_exempt
@require_http_methods(["POST"])
def process_text(request):
    """Procesa texto ingresado manualmente"""
    try:
        # Check if it's JSON data (AJAX request) or form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            title = data.get('title', 'Texto sin título')
            text_content = data.get('text', '')
        else:
            # Form data
            title = request.POST.get('title', 'Texto sin título')
            text_content = request.POST.get('text', '')
        
        if not text_content.strip():
            messages.error(request, 'El texto no puede estar vacío')
            return redirect('resumenes:home')
        
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
        
        # *** REGISTRAR EN HISTORIAL ***
        # Detectar el tema principal del texto (primeras palabras)
        tema_principal = text_content.strip()[:50] + "..." if len(text_content) > 50 else text_content.strip()
        
        registrar_actividad(
            tipo='resumen_creado',
            titulo=title,
            descripcion=f'Desde texto • {tema_principal}',
            app_origen='resumenes',
            objeto_id=document.id,
            metadata={
                'document_type': 'manual',
                'palabras_resumen': len(summary_text.split()),
                'palabras_original': len(text_content.split()),
                'fuente': 'texto'
            }
        )
        
        messages.success(request, 'Texto procesado exitosamente')
        return redirect('resumenes:view_summary', document_id=document.id)
        
    except json.JSONDecodeError:
        messages.error(request, 'Error en el formato de datos')
        return redirect('resumenes:home')
    except Exception as e:
        messages.error(request, f'Error al procesar texto: {str(e)}')
        return redirect('resumenes:home')

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

def mis_resumenes(request):
    """Vista para mostrar todos los resúmenes creados"""
    try:
        # Obtener todos los documentos con sus resúmenes
        documents = Document.objects.filter(
            summary__isnull=False
        ).select_related('summary').order_by('-created_at')
        
        # Preparar datos con estadísticas
        resumenes_data = []
        for document in documents:
            try:
                summary = document.summary
                resumenes_data.append({
                    'document': document,
                    'summary': summary,
                    'palabras_original': len(document.original_text.split()) if document.original_text else 0,
                    'palabras_resumen': len(summary.summary_text.split()) if summary.summary_text else 0,
                })
            except Exception as e:
                print(f"Error procesando documento {document.id}: {e}")
                continue
        
        context = {
            'resumenes_data': resumenes_data,
            'total_resumenes': len(resumenes_data),
        }
        
        return render(request, 'resumenes/mis_resumenes.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar resúmenes: {str(e)}')
        return redirect('resumenes:home')

def ver_resumen(request, id):
    """Vista para ver un resumen específico por ID"""
    try:
        document = get_object_or_404(Document, id=id)
        
        try:
            summary = document.summary
        except Summary.DoesNotExist:
            messages.error(request, 'No se encontró resumen para este documento.')
            return redirect('resumenes:home')
        
        context = {
            'document': document,
            'summary': summary,
        }
        
        return render(request, 'resumenes/summary.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar el resumen: {str(e)}')
        return redirect('resumenes:home')

def exportar_pdf(request, id):
    """Exportar resumen a PDF"""
    document = get_object_or_404(Document, id=id)
    
    try:
        summary = document.summary
    except Summary.DoesNotExist:
        messages.error(request, 'No se encontró resumen para este documento.')
        return redirect('resumenes:ver_resumen', id=id)
    
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
        story.append(Paragraph(document.title, title_style))
        story.append(Spacer(1, 12))
        
        # Metadatos
        story.append(Paragraph(f"<b>Tipo:</b> {document.document_type.upper()}", styles['Normal']))
        story.append(Paragraph(f"<b>Creado:</b> {document.created_at.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        if document.original_text:
            story.append(Paragraph(f"<b>Palabras originales:</b> {len(document.original_text.split())}", styles['Normal']))
        story.append(Paragraph(f"<b>Palabras del resumen:</b> {len(summary.summary_text.split())}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Resumen
        story.append(Paragraph("Resumen", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Dividir el resumen en párrafos
        paragraphs = summary.summary_text.split('\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Generar PDF
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Resumen_{document.title}.pdf"'
        return response
        
    except ImportError:
        messages.error(request, 'Funcionalidad de PDF no disponible. Instala reportlab.')
        return redirect('resumenes:ver_resumen', id=id)
    except Exception as e:
        messages.error(request, f'Error al generar PDF: {str(e)}')
        return redirect('resumenes:ver_resumen', id=id)

def confirmar_eliminar_resumen(request, id):
    """Vista de confirmación antes de eliminar un resumen"""
    document = get_object_or_404(Document, id=id)
    
    # Si es POST, eliminar directamente
    if request.method == 'POST':
        titulo = document.title
        document.delete()  # Esto también eliminará el summary por CASCADE
        messages.success(request, f'Resumen "{titulo}" eliminado correctamente.')
        return redirect('resumenes:mis_resumenes')
    
    # Si es GET, mostrar página de confirmación
    context = {'document': document}
    return render(request, 'resumenes/confirmar_eliminar.html', context)

def eliminar_resumen(request, id):
    """Vista para eliminar definitivamente un resumen - redirige a confirmar"""
    return redirect('resumenes:confirmar_eliminar_resumen', id=id)