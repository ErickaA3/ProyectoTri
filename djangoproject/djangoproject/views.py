# views.py - En tu proyecto principal - CON QUICK SORT
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import json
import pytz

# Importar Quick Sort desde historial
from historial.sorting import quick_sort_historial

def home(request):
    """Vista principal del home"""
    return render(request, 'home.html')

def obtener_historial(request):
    """Vista AJAX para obtener el historial con ordenamiento Quick Sort"""
    try:
        print("DEBUG: Vista obtener_historial llamada")
        print(f"DEBUG: Parámetros GET: {request.GET}")
        
        # Importar aquí para evitar problemas de importación circular
        from historial.models import ActividadHistorial
        
        # Obtener parámetros de la petición
        algoritmo = request.GET.get('algoritmo', 'quick')
        orden = request.GET.get('orden', 'desc')
        dias = int(request.GET.get('dias', 4))
        
        print(f"DEBUG: algoritmo={algoritmo}, orden={orden}, dias={dias}")
        
        # Validar días (máximo 7)
        if dias > 7:
            dias = 7
        
        orden_descendente = orden.lower() == 'desc'
        
        # Obtener actividades de los últimos N días
        fecha_limite = timezone.now() - timedelta(days=dias)
        actividades = ActividadHistorial.objects.filter(
            fecha_creacion__gte=fecha_limite
        )
        
        print(f"DEBUG: Actividades encontradas en BD: {actividades.count()}")
        
        # Convertir a lista de diccionarios para ordenamiento
        actividades_data = []
        for actividad in actividades:
            actividades_data.append({
                'id': actividad.id,
                'fecha_creacion': actividad.fecha_creacion,
                'tipo': actividad.tipo,
                'titulo': actividad.titulo,
                'descripcion': actividad.descripcion,
                'metadata': actividad.metadata,
                'app_origen': actividad.app_origen,
                'objeto_id': actividad.objeto_id,
            })
        
        print(f"DEBUG: Lista para ordenar: {len(actividades_data)} elementos")
        
        # APLICAR QUICK SORT
        actividades_ordenadas = quick_sort_historial(
            actividades_data, 
            orden_descendente=orden_descendente
        )
        
        print(f"DEBUG: Después de Quick Sort: {len(actividades_ordenadas)} elementos")
        
        # Zona horaria de Costa Rica
        tz_costa_rica = pytz.timezone('America/Costa_Rica')
        
        # Agrupar por día después del ordenamiento
        historial_por_dia = defaultdict(list)
        
        for actividad in actividades_ordenadas:
            # Convertir fecha a Costa Rica
            fecha_cr = actividad['fecha_creacion'].astimezone(tz_costa_rica)
            fecha_str = fecha_cr.strftime('%Y-%m-%d')
            fecha_display = formatear_fecha(actividad['fecha_creacion'])
            
            actividad_formateada = {
                'tipo': actividad['tipo'],
                'titulo': actividad['titulo'],
                'descripcion': actividad['descripcion'],
                'hora': fecha_cr.strftime('%H:%M'),
                'metadata': actividad['metadata'],
                'app_origen': actividad['app_origen'],
                'objeto_id': actividad['objeto_id'],
            }
            
            if fecha_str not in historial_por_dia:
                historial_por_dia[fecha_str] = {
                    'fecha_display': fecha_display,
                    'actividades': []
                }
            
            historial_por_dia[fecha_str]['actividades'].append(actividad_formateada)
        
        # Convertir a lista y ordenar días
        historial_ordenado = []
        fechas_dias = list(historial_por_dia.keys())
        
        # Ordenar las fechas de los días usando el mismo criterio
        if orden_descendente:
            fechas_dias.sort(reverse=True)
        else:
            fechas_dias.sort()
        
        for fecha in fechas_dias:
            dia_data = historial_por_dia[fecha]
            dia_data['count'] = len(dia_data['actividades'])
            dia_data['fecha_key'] = fecha
            historial_ordenado.append(dia_data)
        
        print(f"DEBUG: Historial final: {len(historial_ordenado)} días")
        
        return JsonResponse({
            'success': True,
            'historial': historial_ordenado,
            'total_dias': len(historial_ordenado),
            'total_actividades': len(actividades_ordenadas),
            'algoritmo_usado': algoritmo,
            'orden': 'descendente' if orden_descendente else 'ascendente',
        })
        
    except Exception as e:
        print(f"ERROR en obtener_historial: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def formatear_fecha(fecha):
    """Formatear fecha para mostrar de forma amigable en horario de Costa Rica"""
    tz_costa_rica = pytz.timezone('America/Costa_Rica')
    
    # Convertir fechas a Costa Rica
    hoy = timezone.now().astimezone(tz_costa_rica).date()
    fecha_actividad = fecha.astimezone(tz_costa_rica).date()
    
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
        fecha_cr = fecha.astimezone(tz_costa_rica)
        mes = meses[fecha_cr.month - 1]
        return f"{fecha_cr.day} de {mes}"

def estadisticas_historial(request):
    """Vista para obtener estadísticas globales del historial"""
    try:
        from historial.utils import obtener_estadisticas_globales
        
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