# historial/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import json
import pytz

# ELIMINAR: from .sorting import quick_sort_historial

# ELIMINAR TODA LA FUNCIÓN obtener_historial DE AQUÍ

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