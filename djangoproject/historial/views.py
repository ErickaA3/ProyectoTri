# views.py - En la app principal donde tienes home.html
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import json
import pytz

def home(request):
    """Vista principal del home"""
    return render(request, 'home.html')

def obtener_historial(request):
    """Vista AJAX para obtener el historial global (sin login)"""
    try:
        # Importar aquí para evitar problemas de importación circular
        from historial.models import ActividadHistorial
        
        # Obtener actividades de los últimos 30 días
        fecha_limite = timezone.now() - timedelta(days=30)
        actividades = ActividadHistorial.objects.filter(
            fecha_creacion__gte=fecha_limite
        ).order_by('-fecha_creacion')
        
        # Agrupar por día
        historial_por_dia = defaultdict(list)
        
        for actividad in actividades:
            fecha_str = actividad.fecha_creacion.strftime('%Y-%m-%d')
            fecha_display = formatear_fecha(actividad.fecha_creacion)
            
            actividad_data = {
                'tipo': actividad.tipo,
                'titulo': actividad.titulo,
                'descripcion': actividad.descripcion,
                'hora': actividad.fecha_creacion.astimezone(pytz.timezone('America/Costa_Rica')).strftime('%H:%M'),
                'metadata': actividad.metadata,
                'app_origen': actividad.app_origen,
                'objeto_id': actividad.objeto_id,
            }
            
            if fecha_str not in historial_por_dia:
                historial_por_dia[fecha_str] = {
                    'fecha_display': fecha_display,
                    'actividades': []
                }
            
            historial_por_dia[fecha_str]['actividades'].append(actividad_data)
        
        # Convertir a lista ordenada
        historial_ordenado = []
        for fecha in sorted(historial_por_dia.keys(), reverse=True):
            dia_data = historial_por_dia[fecha]
            dia_data['count'] = len(dia_data['actividades'])
            historial_ordenado.append(dia_data)
        
        return JsonResponse({
            'success': True,
            'historial': historial_ordenado,
            'total_dias': len(historial_ordenado)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def formatear_fecha(fecha):
    """Formatear fecha para mostrar de forma amigable"""
    hoy = timezone.now().date()
    fecha_actividad = fecha.date()
    
    if fecha_actividad == hoy:
        return "Hoy"
    elif fecha_actividad == hoy - timedelta(days=1):
        return "Ayer"
    elif fecha_actividad >= hoy - timedelta(days=7):
        dias_diff = (hoy - fecha_actividad).days
        return f"Hace {dias_diff} días"
    else:
        meses = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
        ]
        mes = meses[fecha.month - 1]
        return f"{fecha.day} de {mes}"

def estadisticas_historial(request):
    """Vista para obtener estadísticas globales del historial"""
    try:
        from historial.utils import obtener_estadisticas_globales
        
        dias = int(request.GET.get('dias', 7))
        stats = obtener_estadisticas_globales(dias)
        
        return JsonResponse({
            'success': True,
            'estadisticas': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)