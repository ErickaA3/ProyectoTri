# historial/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import json
import pytz

# ← IMPORTAMOS NUESTRO QUICK SORT
from .sorting import quick_sort_historial

def formatear_fecha(fecha):
    """Formatear fecha para mostrar de forma amigable"""
    hoy = timezone.now().date()
    fecha_actividad = fecha.date()
   
    if fecha_actividad == hoy:
        return "Hoy"
    elif fecha_actividad == hoy - timedelta(days=1):
        return "Ayer"
    elif fecha_actividad == hoy - timedelta(days=2):
        return "Anteayer"
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
    """Vista para obtener estadísticas básicas del historial"""
    try:
        from .utils import obtener_estadisticas_globales
       
        dias = int(request.GET.get('dias', 4))
        if dias > 7:
            dias = 7
           
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

def historial_actividades(request):
    """Nueva vista que usa Quick Sort para mostrar el historial"""
    try:
        from .models import ActividadHistorial
        
        # Obtener parámetros
        dias = int(request.GET.get('dias', 30))
        orden = request.GET.get('orden', 'desc')  # 'desc' o 'asc'
        
        # Obtener datos de la BD sin ordenar
        fecha_limite = timezone.now() - timedelta(days=dias)
        actividades = ActividadHistorial.objects.filter(
            fecha_creacion__gte=fecha_limite
        )
        
        # Convertir a lista de diccionarios
        actividades_dict = []
        for actividad in actividades:
            actividades_dict.append({
                'id': actividad.id,
                'tipo': actividad.tipo,
                'titulo': actividad.titulo,
                'descripcion': actividad.descripcion,
                'app_origen': actividad.app_origen,
                'fecha_creacion': actividad.fecha_creacion.isoformat(),
                'fecha_formateada': formatear_fecha(actividad.fecha_creacion),
                'metadata': actividad.metadata,
            })
        
        # ¡USAR NUESTRO QUICK SORT!
        orden_descendente = orden == 'desc'
        actividades_ordenadas = quick_sort_historial(actividades_dict, orden_descendente)
        
        return JsonResponse({
            'success': True,
            'actividades': actividades_ordenadas,
            'total': len(actividades_ordenadas),
            'orden_aplicado': 'descendente' if orden_descendente else 'ascendente',
            'algoritmo_usado': 'Quick Sort personalizado'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def comparar_algoritmos(request):
    """Vista para comparar Quick Sort vs order_by de Django"""
    try:
        from .models import ActividadHistorial
        import time
        
        dias = int(request.GET.get('dias', 7))
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        # Método 1: Django order_by
        start_time = time.time()
        actividades_django = list(ActividadHistorial.objects.filter(
            fecha_creacion__gte=fecha_limite
        ).order_by('-fecha_creacion').values())
        tiempo_django = time.time() - start_time
        
        # Método 2: Quick Sort personalizado
        start_time = time.time()
        actividades = ActividadHistorial.objects.filter(
            fecha_creacion__gte=fecha_limite
        )
        
        actividades_dict = []
        for actividad in actividades:
            actividades_dict.append({
                'id': actividad.id,
                'tipo': actividad.tipo,
                'titulo': actividad.titulo,
                'fecha_creacion': actividad.fecha_creacion,
                'app_origen': actividad.app_origen,
            })
        
        actividades_quicksort = quick_sort_historial(actividades_dict)
        tiempo_quicksort = time.time() - start_time
        
        return JsonResponse({
            'success': True,
            'comparacion': {
                'django_order_by': {
                    'tiempo_ms': round(tiempo_django * 1000, 2),
                    'registros': len(actividades_django)
                },
                'quick_sort_personalizado': {
                    'tiempo_ms': round(tiempo_quicksort * 1000, 2),
                    'registros': len(actividades_quicksort)
                }
            },
            'ganador': 'Django' if tiempo_django < tiempo_quicksort else 'Quick Sort'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)