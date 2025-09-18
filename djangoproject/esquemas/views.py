# esquemas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

from .models import Esquema, NodoEsquema, EventoTimeline, ConceptoMapa
from .utils import (
    extraer_texto_archivo, 
    generar_esquema_openai,
    crear_nodos_desde_json,
    crear_eventos_desde_json,
    crear_conceptos_desde_json
)

def get_or_create_default_user():
    """Crear o obtener un usuario por defecto para testing"""
    user, created = User.objects.get_or_create(
        username='usuario_default',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Usuario',
            'last_name': 'Default'
        }
    )
    return user

def esquemas_home(request):
    """Vista principal de esquemas"""
    esquemas_recientes = Esquema.objects.all().order_by('-fecha_creacion')[:5]
    context = {
        'esquemas_recientes': esquemas_recientes,
    }
    return render(request, 'esquemas/esquemas_home.html', context)

def crear_desde_texto(request):
    """Vista para crear esquema desde texto"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        tipo = request.POST.get('tipo')
        contenido_texto = request.POST.get('contenido_texto')
        
        if not titulo or not tipo or not contenido_texto:
            messages.error(request, 'Todos los campos son requeridos.')
            return render(request, 'esquemas/esquemas_home.html')
        
        try:
            # Generar esquema con OpenAI
            datos_esquema = generar_esquema_openai(contenido_texto, tipo)
            
            # Obtener usuario por defecto
            usuario_default = get_or_create_default_user()
            
            # Crear el esquema en la base de datos
            esquema = Esquema.objects.create(
                titulo=titulo,
                tipo=tipo,
                fuente='texto',
                contenido_original=contenido_texto,
                contenido_procesado=datos_esquema,
                usuario=usuario_default
            )
            
            # Crear elementos específicos según el tipo
            if tipo == 'jerarquico':
                crear_nodos_desde_json(esquema, datos_esquema)
            elif tipo == 'cronologico':
                crear_eventos_desde_json(esquema, datos_esquema)
            elif tipo == 'conceptual':
                crear_conceptos_desde_json(esquema, datos_esquema)
            
            messages.success(request, f'Esquema "{titulo}" creado exitosamente!')
            return redirect('esquemas:ver_esquema', esquema_id=esquema.id)
            
        except Exception as e:
            messages.error(request, f'Error al generar el esquema: {str(e)}')
            return render(request, 'esquemas/esquemas_home.html')
    
    return render(request, 'esquemas/esquemas_home.html')

def crear_desde_archivo(request):
    """Vista para crear esquema desde archivo"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        tipo = request.POST.get('tipo')
        archivo = request.FILES.get('archivo')
        
        if not titulo or not tipo or not archivo:
            messages.error(request, 'Todos los campos son requeridos.')
            return render(request, 'esquemas/esquemas_home.html')
        
        # Validar archivo
        if archivo.size > 10 * 1024 * 1024:  # 10MB
            messages.error(request, 'El archivo es demasiado grande. El tamaño máximo es 10MB.')
            return render(request, 'esquemas/esquemas_home.html')
        
        nombre = archivo.name.lower()
        extensiones_validas = ['.pdf', '.doc', '.docx', '.txt']
        if not any(nombre.endswith(ext) for ext in extensiones_validas):
            messages.error(request, 'Formato de archivo no válido. Solo se permiten PDF, DOC, DOCX y TXT.')
            return render(request, 'esquemas/esquemas_home.html')
        
        try:
            # Extraer texto del archivo
            contenido_texto = extraer_texto_archivo(archivo)
            
            # Generar esquema con OpenAI
            datos_esquema = generar_esquema_openai(contenido_texto, tipo)
            
            # Obtener usuario por defecto
            usuario_default = get_or_create_default_user()
            
            # Crear el esquema en la base de datos
            esquema = Esquema.objects.create(
                titulo=titulo,
                tipo=tipo,
                fuente='archivo',
                contenido_original=contenido_texto,
                contenido_procesado=datos_esquema,
                archivo_original=archivo,
                usuario=usuario_default
            )
            
            # Crear elementos específicos según el tipo
            if tipo == 'jerarquico':
                crear_nodos_desde_json(esquema, datos_esquema)
            elif tipo == 'cronologico':
                crear_eventos_desde_json(esquema, datos_esquema)
            elif tipo == 'conceptual':
                crear_conceptos_desde_json(esquema, datos_esquema)
            
            messages.success(request, f'Esquema "{titulo}" creado exitosamente desde archivo!')
            return redirect('esquemas:ver_esquema', esquema_id=esquema.id)
            
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            return render(request, 'esquemas/esquemas_home.html')
    
    return render(request, 'esquemas/esquemas_home.html')

def ver_esquema(request, esquema_id):
    """Vista para mostrar un esquema específico"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    context = {
        'esquema': esquema,
    }
    
    # Cargar datos específicos según el tipo de esquema
    if esquema.tipo == 'jerarquico':
        context['nodos'] = esquema.nodos.all()
    elif esquema.tipo == 'cronologico':
        context['eventos'] = esquema.eventos.all()
    elif esquema.tipo == 'conceptual':
        context['conceptos'] = esquema.conceptos.all()
        context['concepto_central'] = esquema.conceptos.filter(es_central=True).first()
        context['conceptos_relacionados'] = esquema.conceptos.filter(es_central=False)
    
    return render(request, 'esquemas/ver_esquema.html', context)

def mis_esquemas(request):
    """Vista para listar todos los esquemas"""
    esquemas = Esquema.objects.all().order_by('-fecha_creacion')
    
    # Filtros opcionales
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro:
        esquemas = esquemas.filter(tipo=tipo_filtro)
    
    context = {
        'esquemas': esquemas,
        'tipo_filtro': tipo_filtro,
        'tipos_disponibles': Esquema.TIPO_CHOICES,
    }
    return render(request, 'esquemas/mis_esquemas.html', context)

def eliminar_esquema(request, esquema_id):
    """Vista para eliminar un esquema"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    if request.method == 'POST':
        titulo = esquema.titulo
        esquema.delete()
        messages.success(request, f'Esquema "{titulo}" eliminado exitosamente.')
        return redirect('esquemas:mis_esquemas')
    
    return render(request, 'esquemas/confirmar_eliminar.html', {'esquema': esquema})

def exportar_esquema_pdf(request, esquema_id):
    """Exporta un esquema a PDF"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, esquema.titulo)
    
    # Metadata
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, f"Tipo: {esquema.get_tipo_display()}")
    p.drawString(50, height - 85, f"Creado: {esquema.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
    
    y = height - 120
    
    if esquema.tipo == 'jerarquico':
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Contenido:")
        y -= 20
        
        for nodo in esquema.nodos.all():
            p.setFont("Helvetica", 10)
            indent = (nodo.nivel - 1) * 20
            text = f"{'  ' * (nodo.nivel - 1)}{nodo.texto}"
            p.drawString(50 + indent, y, text[:80])
            y -= 15
            if y < 100:  # Nueva página si es necesario
                p.showPage()
                y = height - 50
    
    elif esquema.tipo == 'cronologico':
        for evento in esquema.eventos.all():
            p.setFont("Helvetica-Bold", 11)
            p.drawString(50, y, f"{evento.fecha}: {evento.titulo}")
            y -= 15
            p.setFont("Helvetica", 10)
            p.drawString(70, y, evento.descripcion[:100])
            y -= 25
            if y < 100:
                p.showPage()
                y = height - 50
    
    elif esquema.tipo == 'conceptual':
        concepto_central = esquema.conceptos.filter(es_central=True).first()
        if concepto_central:
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, f"Concepto Central: {concepto_central.texto}")
            y -= 30
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Conceptos Relacionados:")
        y -= 20
        
        for concepto in esquema.conceptos.filter(es_central=False):
            p.setFont("Helvetica", 10)
            p.drawString(70, y, f"• {concepto.texto}")
            y -= 12
            if concepto.descripcion:
                p.drawString(85, y, concepto.descripcion[:80])
                y -= 12
            y -= 5
            if y < 100:
                p.showPage()
                y = height - 50
    
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="esquema_{esquema.id}.pdf"'
    return response

def exportar_esquema_txt(request, esquema_id):
    """Exporta un esquema a TXT"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    contenido = f"{esquema.titulo}\n"
    contenido += f"Tipo: {esquema.get_tipo_display()}\n"
    contenido += f"Creado: {esquema.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\n"
    contenido += "="*50 + "\n\n"
    
    if esquema.tipo == 'jerarquico':
        for nodo in esquema.nodos.all():
            indent = "  " * (nodo.nivel - 1)
            contenido += f"{indent}• {nodo.texto}\n"
    
    elif esquema.tipo == 'cronologico':
        for evento in esquema.eventos.all():
            contenido += f"{evento.fecha}: {evento.titulo}\n"
            contenido += f"  {evento.descripcion}\n\n"
    
    elif esquema.tipo == 'conceptual':
        concepto_central = esquema.conceptos.filter(es_central=True).first()
        if concepto_central:
            contenido += f"CONCEPTO CENTRAL: {concepto_central.texto}\n\n"
        
        contenido += "CONCEPTOS RELACIONADOS:\n"
        for concepto in esquema.conceptos.filter(es_central=False):
            contenido += f"• {concepto.texto}\n"
            if concepto.descripcion:
                contenido += f"  {concepto.descripcion}\n"
            contenido += "\n"
    
    response = HttpResponse(contenido, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="esquema_{esquema.id}.txt"'
    return response

@require_http_methods(["GET"])
def api_esquema_datos(request, esquema_id):
    """API para obtener datos del esquema en formato JSON"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    datos = {
        'id': esquema.id,
        'titulo': esquema.titulo,
        'tipo': esquema.tipo,
        'fecha_creacion': esquema.fecha_creacion.isoformat(),
        'contenido_procesado': esquema.contenido_procesado
    }
    
    return JsonResponse(datos)