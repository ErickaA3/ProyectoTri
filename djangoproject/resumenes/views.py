<<<<<<< HEAD
# resumenes/views.py - CÓDIGO COMPLETO ACTUALIZADO
from django.shortcuts import render, redirect
=======
from django.shortcuts import render, redirect, get_object_or_404
>>>>>>> a8298e51a1371723a3ef8f03f760a35f55687659
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.urls import reverse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import json
import io
import textwrap
from .models import Document, Summary
from .forms import DocumentForm, TextForm
from .utils import extract_text_from_file, generate_summary_with_openai, generate_outline_with_openai

# IMPORTAR HISTORIAL
from historial.utils import registrar_actividad

def home(request):
    """Vista principal con las tarjetas y resúmenes recientes"""
    # Obtener los 6 resúmenes más recientes
    resumenes_recientes = None
    if request.user.is_authenticated:
        resumenes_recientes = Document.objects.filter(
            user=request.user,
            summary__isnull=False
        ).select_related('summary')[:6]
    else:
        # Para usuarios no autenticados, mostrar los últimos generales
        resumenes_recientes = Document.objects.filter(
            summary__isnull=False
        ).select_related('summary')[:6]
    
    context = {
        'titulo': 'Procesamiento de Documentos',
        'descripcion': 'Sube archivos o ingresa texto para generar resúmenes automáticos',
        'resumenes_recientes': resumenes_recientes
    }
    return render(request, 'resumenes/resumenes_home.html', context)

@require_http_methods(["POST"])
def process_file(request):
    """Procesa archivos subidos via formulario normal"""
    try:
        if 'file' not in request.FILES:
            messages.error(request, 'No se encontró archivo')
            return redirect('resumenes:home')
        
        file = request.FILES['file']
        title = request.POST.get('title', file.name.split('.')[0])
        
        if not title.strip():
            title = file.name.split('.')[0]
        
        # Validar tamaño del archivo (10MB max)
        if file.size > 10 * 1024 * 1024:
            messages.error(request, 'El archivo es demasiado grande. Máximo 10MB.')
            return redirect('resumenes:home')
        
        # Validar tipo de archivo
        allowed_extensions = ['pdf', 'txt', 'doc', 'docx']
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            messages.error(request, f'Tipo de archivo no soportado. Use: {", ".join(allowed_extensions)}')
            return redirect('resumenes:home')
        
        # Extraer texto del archivo
        try:
            text_content = extract_text_from_file(file)
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            return redirect('resumenes:home')
        
        if not text_content.strip():
            messages.error(request, 'El archivo está vacío o no se pudo extraer texto.')
            return redirect('resumenes:home')
        
        # Crear documento en la base de datos
        document = Document.objects.create(
            title=title,
            document_type=file_extension,
            original_file=file,
            original_text=text_content,
            user=request.user if request.user.is_authenticated else None
        )
        
        # Generar resumen con OpenAI
        try:
            summary_text = generate_summary_with_openai(text_content)
        except Exception as e:
            messages.error(request, f'Error al generar el resumen: {str(e)}')
            document.delete()  # Eliminar documento si falla la generación
            return redirect('resumenes:home')
        
        # Guardar resumen
        summary = Summary.objects.create(
            document=document,
            summary_text=summary_text
        )
        
<<<<<<< HEAD
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
        
        return JsonResponse({
            'success': True,
            'document_id': document.id,
            'summary': summary_text,
            'message': 'Archivo procesado exitosamente'
        })
=======
        messages.success(request, 'Archivo procesado exitosamente')
        return redirect('resumenes:view_summary', document_id=document.id)
>>>>>>> a8298e51a1371723a3ef8f03f760a35f55687659
        
    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
        return redirect('resumenes:home')

@require_http_methods(["POST"])
def process_text(request):
    """Procesa texto ingresado manualmente via formulario normal"""
    try:
        title = request.POST.get('title', '').strip()
        text_content = request.POST.get('text', '').strip()
        
        if not title:
            messages.error(request, 'El título es requerido')
            return redirect('resumenes:home')
            
        if not text_content:
            messages.error(request, 'El texto no puede estar vacío')
            return redirect('resumenes:home')
        
        if len(text_content) < 50:
            messages.error(request, 'El texto debe tener al menos 50 caracteres para generar un resumen útil')
            return redirect('resumenes:home')
        
        # Crear documento en la base de datos
        document = Document.objects.create(
            title=title,
            document_type='manual',
            original_text=text_content,
            user=request.user if request.user.is_authenticated else None
        )
        
        # Generar resumen con OpenAI
        try:
            summary_text = generate_summary_with_openai(text_content)
        except Exception as e:
            messages.error(request, f'Error al generar el resumen: {str(e)}')
            document.delete()  # Eliminar documento si falla la generación
            return redirect('resumenes:home')
        
        # Guardar resumen
        summary = Summary.objects.create(
            document=document,
            summary_text=summary_text
        )
        
<<<<<<< HEAD
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
        
        return JsonResponse({
            'success': True,
            'document_id': document.id,
            'summary': summary_text,
            'message': 'Texto procesado exitosamente'
        })
=======
        messages.success(request, 'Texto procesado exitosamente')
        return redirect('resumenes:view_summary', document_id=document.id)
>>>>>>> a8298e51a1371723a3ef8f03f760a35f55687659
        
    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
        return redirect('resumenes:home')

def view_summary(request, document_id):
    """Muestra el resumen generado"""
    try:
        document = get_object_or_404(Document, id=document_id)
        summary = get_object_or_404(Summary, document=document)
        
        context = {
            'document': document,
            'summary': summary,
        }
        return render(request, 'resumenes/summary.html', context)
    
    except Exception as e:
        messages.error(request, 'Documento no encontrado')
<<<<<<< HEAD
        return redirect('resumenes:home')
=======
        return redirect('resumenes:home')

def mis_resumenes(request):
    """Lista todos los resúmenes del usuario"""
    if request.user.is_authenticated:
        resumenes = Document.objects.filter(
            user=request.user,
            summary__isnull=False
        ).select_related('summary').order_by('-created_at')
    else:
        resumenes = Document.objects.filter(
            summary__isnull=False
        ).select_related('summary').order_by('-created_at')
    
    # Paginación
    paginator = Paginator(resumenes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'resumenes': page_obj,
        'total_resumenes': resumenes.count()
    }
    return render(request, 'resumenes/mis_resumenes.html', context)

def ver_resumen(request, id):
    """Ver un resumen específico (alias para view_summary)"""
    return view_summary(request, id)

def exportar_pdf(request, id):
    """Exportar resumen como PDF usando ReportLab"""
    try:
        document = get_object_or_404(Document, id=id)
        summary = get_object_or_404(Summary, document=document)
        
        # Crear buffer en memoria
        buffer = io.BytesIO()
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Obtener estilos
        styles = getSampleStyleSheet()
        
        # Crear estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor='black',
            alignment=1  # Centrado
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor='blue'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=0  # Justificado
        )
        
        # Título del documento
        story.append(Paragraph(f"RESUMEN: {document.title}", title_style))
        story.append(Spacer(1, 12))
        
        # Información del documento
        story.append(Paragraph("INFORMACIÓN DEL DOCUMENTO", header_style))
        
        info_text = f"""
        <b>Tipo:</b> {document.get_document_type_display()}<br/>
        <b>Procesado el:</b> {summary.created_at.strftime('%d/%m/%Y a las %H:%M')}<br/>
        <b>Caracteres originales:</b> {len(document.original_text):,}<br/>
        <b>Fuente:</b> {'Archivo subido' if document.original_file else 'Texto directo'}
        """
        
        story.append(Paragraph(info_text, normal_style))
        story.append(Spacer(1, 24))
        
        # Contenido del resumen
        story.append(Paragraph("CONTENIDO DEL RESUMEN", header_style))
        
        # Procesar el texto del resumen - dividir en párrafos
        summary_paragraphs = summary.summary_text.split('\n\n')
        
        for paragraph in summary_paragraphs:
            if paragraph.strip():
                # Limpiar y formatear el párrafo
                clean_paragraph = paragraph.strip().replace('\n', ' ')
                story.append(Paragraph(clean_paragraph, normal_style))
                story.append(Spacer(1, 6))
        
        # Pie de página
        story.append(Spacer(1, 36))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor='gray',
            alignment=1  # Centrado
        )
        
        story.append(Paragraph("---", footer_style))
        story.append(Paragraph("Generado por FocusPy", footer_style))
        story.append(Paragraph(f"Documento creado el {summary.created_at.strftime('%d de %B de %Y')}", footer_style))
        
        # Construir PDF
        doc.build(story)
        
        # Obtener el valor del buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Crear respuesta HTTP
        response = HttpResponse(pdf, content_type='application/pdf')
        
        # Generar nombre de archivo seguro
        safe_filename = "".join(c for c in document.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_filename = safe_filename.replace(' ', '_')[:50]  # Limitar longitud
        
        response['Content-Disposition'] = f'attachment; filename="resumen_{safe_filename}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al exportar el resumen: {str(e)}')
        return redirect('resumenes:view_summary', document_id=id)

def confirmar_eliminar_resumen(request, id):
    """Vista para confirmar eliminación de resumen"""
    resumen = get_object_or_404(Document, id=id)
    
    # Verificar permisos si el usuario está autenticado
    if request.user.is_authenticated and resumen.user and resumen.user != request.user:
        messages.error(request, 'No tienes permisos para eliminar este resumen')
        return redirect('resumenes:mis_resumenes')
    
    if request.method == 'POST':
        # Si confirma, eliminar
        titulo = resumen.title
        resumen.delete()  # Esto eliminará también el summary por CASCADE
        
        messages.success(request, f'Resumen "{titulo}" eliminado correctamente')
        return redirect('resumenes:mis_resumenes')
    
    # Mostrar página de confirmación
    context = {
        'resumen': resumen
    }
    return render(request, 'resumenes/confirmar_eliminar_resumen.html', context)

def eliminar_resumen(request, id):
    """Función de eliminación directa (para mantener compatibilidad)"""
    return confirmar_eliminar_resumen(request, id)
>>>>>>> a8298e51a1371723a3ef8f03f760a35f55687659
