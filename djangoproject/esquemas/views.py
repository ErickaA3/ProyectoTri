# esquemas/views.py - CÓDIGO COMPLETO ACTUALIZADO
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db import transaction
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

# IMPORTAR HISTORIAL
from historial.utils import registrar_actividad

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
    esquemas_recientes = Esquema.objects.all().order_by('-fecha_creacion')[:6]
    todos_esquemas = Esquema.objects.all()
    
    context = {
        'esquemas_recientes': esquemas_recientes,
        'todos_esquemas': todos_esquemas,
    }
    return render(request, 'esquemas/esquemas_home.html', context)

def crear_desde_texto(request):
    """Vista para crear esquema desde texto - VERSIÓN MEJORADA"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        tipo = request.POST.get('tipo')
        contenido_texto = request.POST.get('contenido_texto')
        
        if not titulo or not tipo or not contenido_texto:
            messages.error(request, 'Todos los campos son requeridos.')
            return render(request, 'esquemas/esquemas_home.html')
        
        try:
            # Generar esquema con OpenAI (función actualizada)
            datos_esquema = generar_esquema_openai(contenido_texto, tipo)
            
            # Obtener usuario por defecto
            usuario = get_or_create_default_user()
            
            with transaction.atomic():
                # Crear el esquema en la base de datos
                esquema = Esquema.objects.create(
                    titulo=titulo,
                    tipo=tipo,
                    fuente='texto',
                    contenido_original=contenido_texto,
                    contenido_procesado=datos_esquema,
                    usuario=usuario
                )
                
                # Crear elementos específicos según el tipo
                if tipo == 'jerarquico':
                    crear_nodos_desde_json(esquema, datos_esquema)
                elif tipo == 'cronologico':
                    crear_eventos_desde_json(esquema, datos_esquema)
                elif tipo == 'conceptual':
                    crear_conceptos_desde_json(esquema, datos_esquema)
            
            # *** REGISTRAR EN HISTORIAL ***
            # Contar elementos según el tipo
            elementos_count = 0
            if tipo == 'jerarquico':
                elementos_count = esquema.nodos.count()
                descripcion = f'Desde texto • {elementos_count} nodos principales'
            elif tipo == 'cronologico':
                elementos_count = esquema.eventos.count()
                descripcion = f'Desde texto • {elementos_count} eventos'
            elif tipo == 'conceptual':
                elementos_count = esquema.conceptos.count()
                descripcion = f'Desde texto • {elementos_count} conceptos relacionados'
            
            registrar_actividad(
                tipo='esquema_generado',
                titulo=titulo,
                descripcion=descripcion,
                app_origen='esquemas',
                objeto_id=esquema.id,
                metadata={
                    'tipo_esquema': tipo,
                    'elementos_count': elementos_count,
                    'fuente': 'texto'
                }
            )
            
            messages.success(request, f'Esquema "{titulo}" creado exitosamente con información expandible!')
            return redirect('esquemas:ver_esquema', esquema_id=esquema.id)
            
        except Exception as e:
            messages.error(request, f'Error al generar el esquema: {str(e)}')
            return render(request, 'esquemas/esquemas_home.html')
    
    return render(request, 'esquemas/esquemas_home.html')

def crear_desde_archivo(request):
    """Vista para crear esquema desde archivo - VERSIÓN MEJORADA"""
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
            
            if not contenido_texto.strip():
                messages.error(request, 'No se pudo extraer texto del archivo')
                return render(request, 'esquemas/esquemas_home.html')
            
            # Generar esquema con OpenAI (función actualizada)
            datos_esquema = generar_esquema_openai(contenido_texto, tipo)
            
            # Obtener usuario por defecto
            usuario = get_or_create_default_user()
            
            with transaction.atomic():
                # Crear el esquema en la base de datos
                esquema = Esquema.objects.create(
                    titulo=titulo,
                    tipo=tipo,
                    fuente='archivo',
                    contenido_original=contenido_texto,
                    contenido_procesado=datos_esquema,
                    archivo_original=archivo,
                    usuario=usuario
                )
                
                # Crear elementos específicos según el tipo
                if tipo == 'jerarquico':
                    crear_nodos_desde_json(esquema, datos_esquema)
                elif tipo == 'cronologico':
                    crear_eventos_desde_json(esquema, datos_esquema)
                elif tipo == 'conceptual':
                    crear_conceptos_desde_json(esquema, datos_esquema)
            
            # *** REGISTRAR EN HISTORIAL ***
            # Contar elementos según el tipo
            elementos_count = 0
            if tipo == 'jerarquico':
                elementos_count = esquema.nodos.count()
                descripcion = f'Desde archivo {archivo.name.split(".")[-1].upper()} • {elementos_count} nodos principales'
            elif tipo == 'cronologico':
                elementos_count = esquema.eventos.count()
                descripcion = f'Desde archivo {archivo.name.split(".")[-1].upper()} • {elementos_count} eventos'
            elif tipo == 'conceptual':
                elementos_count = esquema.conceptos.count()
                descripcion = f'Desde archivo {archivo.name.split(".")[-1].upper()} • {elementos_count} conceptos relacionados'
            
            registrar_actividad(
                tipo='esquema_generado',
                titulo=titulo,
                descripcion=descripcion,
                app_origen='esquemas',
                objeto_id=esquema.id,
                metadata={
                    'tipo_esquema': tipo,
                    'elementos_count': elementos_count,
                    'fuente': 'archivo',
                    'archivo_nombre': archivo.name
                }
            )
            
            messages.success(request, f'Esquema "{titulo}" creado exitosamente desde archivo con detalles expandibles!')
            return redirect('esquemas:ver_esquema', esquema_id=esquema.id)
            
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            return render(request, 'esquemas/esquemas_home.html')
    
    return render(request, 'esquemas/esquemas_home.html')

def ver_esquema(request, esquema_id):
    """Vista para mostrar un esquema específico - VERSIÓN MEJORADA"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    context = {'esquema': esquema}
    
    # Cargar datos específicos según el tipo de esquema
    if esquema.tipo == 'jerarquico':
        # Intentar obtener nodos de la base de datos primero
        nodos = esquema.nodos.all().order_by('nivel', 'orden')
        
        # Si no hay nodos en BD, crearlos desde el JSON
        if not nodos.exists() and esquema.contenido_procesado:
            try:
                print(f"DEBUG: Creando nodos desde JSON para esquema {esquema.id}")
                crear_nodos_desde_json(esquema, esquema.contenido_procesado)
                nodos = esquema.nodos.all().order_by('nivel', 'orden')
                messages.info(request, 'Estructura jerárquica regenerada automáticamente')
            except Exception as e:
                print(f"ERROR creando nodos: {e}")
                messages.warning(request, f'Error al cargar estructura jerárquica: {str(e)}')
                nodos = []
        
        context['nodos'] = nodos
        
        # Para debug: también pasar el JSON original
        if request.GET.get('debug'):
            context['debug_json'] = esquema.contenido_procesado
            context['debug_nodos_count'] = nodos.count()
        
    elif esquema.tipo == 'cronologico':
        # Eventos de la línea de tiempo
        eventos = esquema.eventos.all().order_by('orden')
        
        # Si no hay eventos, crearlos desde JSON
        if not eventos.exists() and esquema.contenido_procesado:
            try:
                crear_eventos_desde_json(esquema, esquema.contenido_procesado)
                eventos = esquema.eventos.all().order_by('orden')
                messages.info(request, 'Línea de tiempo regenerada automáticamente')
            except Exception as e:
                messages.warning(request, f'Error al cargar línea de tiempo: {str(e)}')
        
        context['eventos'] = eventos
        
    elif esquema.tipo == 'conceptual':
        # Conceptos del mapa
        conceptos = esquema.conceptos.all()
        concepto_central = conceptos.filter(es_central=True).first()
        conceptos_relacionados = conceptos.filter(es_central=False)
        
        # Si no hay conceptos, crearlos desde JSON
        if not conceptos.exists() and esquema.contenido_procesado:
            try:
                crear_conceptos_desde_json(esquema, esquema.contenido_procesado)
                conceptos = esquema.conceptos.all()
                concepto_central = conceptos.filter(es_central=True).first()
                conceptos_relacionados = conceptos.filter(es_central=False)
                messages.info(request, 'Mapa conceptual regenerado automáticamente')
            except Exception as e:
                messages.warning(request, f'Error al cargar mapa conceptual: {str(e)}')
        
        context.update({
            'concepto_central': concepto_central,
            'conceptos_relacionados': conceptos_relacionados
        })
    
    return render(request, 'esquemas/ver_esquema.html', context)

def mis_esquemas(request):
    """Vista para listar todos los esquemas"""
    esquemas = Esquema.objects.all().order_by('-fecha_creacion')
    
    # Filtros opcionales
    tipo_filtro = request.GET.get('tipo')
    fuente_filtro = request.GET.get('fuente')
    busqueda = request.GET.get('q')
    
    if tipo_filtro:
        esquemas = esquemas.filter(tipo=tipo_filtro)
    
    if fuente_filtro:
        esquemas = esquemas.filter(fuente=fuente_filtro)
    
    if busqueda:
        esquemas = esquemas.filter(titulo__icontains=busqueda)
    
    context = {
        'esquemas': esquemas,
        'tipo_filtro': tipo_filtro,
        'fuente_filtro': fuente_filtro,
        'busqueda': busqueda,
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
        return redirect('esquemas:home')
    
    return render(request, 'esquemas/confirmar_eliminar.html', {'esquema': esquema})

def exportar_pdf(request, esquema_id):
    """Exportar esquema a PDF"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import io
        
        # Crear buffer para el PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título principal
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
        )
        story.append(Paragraph(esquema.titulo, title_style))
        story.append(Spacer(1, 12))
        
        # Metadatos
        story.append(Paragraph(f"Tipo: {esquema.get_tipo_display()}", styles['Normal']))
        story.append(Paragraph(f"Creado: {esquema.fecha_creacion.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Contenido según tipo
        if esquema.tipo == 'jerarquico':
            nodos = esquema.nodos.all().order_by('nivel', 'orden')
            for nodo in nodos:
                indent = "&nbsp;" * (nodo.nivel - 1) * 8
                texto = f"{indent}{nodo.texto}"
                story.append(Paragraph(texto, styles['Normal']))
                story.append(Spacer(1, 6))
                
        elif esquema.tipo == 'conceptual':
            conceptos = esquema.conceptos.all()
            concepto_central = conceptos.filter(es_central=True).first()
            if concepto_central:
                story.append(Paragraph(f"<b>Concepto Central:</b> {concepto_central.texto}", styles['Heading2']))
                story.append(Spacer(1, 12))
            
            conceptos_relacionados = conceptos.filter(es_central=False)
            for concepto in conceptos_relacionados:
                story.append(Paragraph(f"• {concepto.texto}", styles['Normal']))
                if concepto.descripcion:
                    story.append(Paragraph(f"  {concepto.descripcion}", styles['Normal']))
                story.append(Spacer(1, 6))
                
        elif esquema.tipo == 'cronologico':
            eventos = esquema.eventos.all().order_by('orden')
            for evento in eventos:
                story.append(Paragraph(f"<b>{evento.fecha}:</b> {evento.titulo}", styles['Heading3']))
                story.append(Paragraph(evento.descripcion, styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Generar PDF
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{esquema.titulo}.pdf"'
        return response
        
    except ImportError:
        messages.error(request, 'Funcionalidad de PDF no disponible. Instala reportlab.')
        return redirect('esquemas:ver_esquema', esquema_id=esquema.id)
    except Exception as e:
        messages.error(request, f'Error al generar PDF: {str(e)}')
        return redirect('esquemas:ver_esquema', esquema_id=esquema.id)

def exportar_txt(request, esquema_id):
    """Exportar esquema a TXT"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    contenido = f"{esquema.titulo}\n"
    contenido += "=" * len(esquema.titulo) + "\n"
    contenido += f"Tipo: {esquema.get_tipo_display()}\n"
    contenido += f"Creado: {esquema.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\n"
    contenido += "=" * 50 + "\n\n"
    
    if esquema.tipo == 'jerarquico':
        nodos = esquema.nodos.all().order_by('nivel', 'orden')
        for nodo in nodos:
            indent = "  " * (nodo.nivel - 1)
            contenido += f"{indent}- {nodo.texto}\n"
            
    elif esquema.tipo == 'conceptual':
        conceptos = esquema.conceptos.all()
        concepto_central = conceptos.filter(es_central=True).first()
        if concepto_central:
            contenido += f"CONCEPTO CENTRAL: {concepto_central.texto}\n\n"
        
        conceptos_relacionados = conceptos.filter(es_central=False)
        contenido += "CONCEPTOS RELACIONADOS:\n"
        for concepto in conceptos_relacionados:
            contenido += f"- {concepto.texto}\n"
            if concepto.descripcion:
                contenido += f"  {concepto.descripcion}\n"
            
    elif esquema.tipo == 'cronologico':
        eventos = esquema.eventos.all().order_by('orden')
        for evento in eventos:
            contenido += f"{evento.fecha}: {evento.titulo}\n"
            contenido += f"{evento.descripcion}\n\n"
    
    response = HttpResponse(contenido, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{esquema.titulo}.txt"'
    return response

# Alias para compatibilidad
def exportar_esquema_pdf(request, esquema_id):
    return exportar_pdf(request, esquema_id)

def exportar_esquema_txt(request, esquema_id):
    return exportar_txt(request, esquema_id)

def debug_esquema(request, esquema_id):
    """Vista de debug para esquemas"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    debug_info = {
        'esquema': {
            'id': esquema.id,
            'titulo': esquema.titulo,
            'tipo': esquema.tipo,
            'usuario': esquema.usuario.username if esquema.usuario else 'Sin usuario',
            'contenido_procesado': esquema.contenido_procesado,
        },
        'nodos_bd': [],
        'nodos_json': esquema.contenido_procesado.get('nodos', []) if esquema.contenido_procesado else [],
        'estadisticas': {}
    }
    
    # Nodos en base de datos
    if esquema.tipo == 'jerarquico':
        nodos = esquema.nodos.all().order_by('nivel', 'orden')
        for nodo in nodos:
            debug_info['nodos_bd'].append({
                'id': nodo.id,
                'texto': nodo.texto[:50] + '...' if len(nodo.texto) > 50 else nodo.texto,
                'nivel': nodo.nivel,
                'orden': nodo.orden,
                'padre_id': nodo.padre.id if nodo.padre else None,
                'hijos_count': nodo.hijos.count()
            })
        
        debug_info['estadisticas'] = {
            'total_nodos_bd': nodos.count(),
            'total_nodos_json': len(debug_info['nodos_json']),
            'niveles_bd': list(nodos.values_list('nivel', flat=True).distinct()),
            'nodos_sin_padre': nodos.filter(padre=None).count()
        }
    
    return JsonResponse(debug_info, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def regenerar_esquema(request, esquema_id):
    """Vista para regenerar un esquema problemático"""
    esquema = get_object_or_404(Esquema, id=esquema_id)
    
    try:
        if esquema.tipo == 'jerarquico':
            esquema.nodos.all().delete()
            crear_nodos_desde_json(esquema, esquema.contenido_procesado)
            messages.success(request, 'Esquema jerárquico regenerado correctamente')
            
        elif esquema.tipo == 'conceptual':
            esquema.conceptos.all().delete()
            crear_conceptos_desde_json(esquema, esquema.contenido_procesado)
            messages.success(request, 'Mapa conceptual regenerado correctamente')
            
        elif esquema.tipo == 'cronologico':
            esquema.eventos.all().delete()
            crear_eventos_desde_json(esquema, esquema.contenido_procesado)
            messages.success(request, 'Línea de tiempo regenerada correctamente')
            
    except Exception as e:
        messages.error(request, f'Error al regenerar esquema: {str(e)}')
    
    return redirect('esquemas:ver_esquema', esquema_id=esquema.id)

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