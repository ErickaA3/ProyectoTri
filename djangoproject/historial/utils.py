# historial/utils.py
from .models import ActividadHistorial
from .sorting import quick_sort_historial  # ← IMPORTAMOS EL QUICK SORT

def registrar_actividad(tipo, titulo, descripcion="", app_origen="", objeto_id=None, metadata=None):
    """
    Función auxiliar para registrar una nueva actividad en el historial
    Sin sistema de usuarios - historial global
    """
    if metadata is None:
        metadata = {}
   
    ActividadHistorial.objects.create(
        tipo=tipo,
        titulo=titulo,
        descripcion=descripcion,
        app_origen=app_origen,
        objeto_id=objeto_id,
        metadata=metadata
    )

def obtener_historial_reciente(dias=30, usar_quicksort=False):
    """
    Obtiene el historial de actividades recientes
    
    Args:
        dias: Número de días hacia atrás (default: 30)
        usar_quicksort: Si True, usa Quick Sort personalizado en lugar del order_by de Django
    
    Returns:
        QuerySet o List de ActividadHistorial
    """
    from django.utils import timezone
    from datetime import timedelta
   
    fecha_limite = timezone.now() - timedelta(days=dias)
    
    if usar_quicksort:
        # Opción 1: Usar Quick Sort personalizado
        actividades = ActividadHistorial.objects.filter(
            fecha_creacion__gte=fecha_limite
        )
        
        # Convertir QuerySet a lista de diccionarios
        actividades_dict = []
        for actividad in actividades:
            actividades_dict.append({
                'id': actividad.id,
                'tipo': actividad.tipo,
                'titulo': actividad.titulo,
                'descripcion': actividad.descripcion,
                'app_origen': actividad.app_origen,
                'fecha_creacion': actividad.fecha_creacion,
                'metadata': actividad.metadata,
            })
        
        # Usar nuestro Quick Sort
        return quick_sort_historial(actividades_dict, orden_descendente=True)
    else:
        # Opción 2: Usar order_by tradicional de Django
        return ActividadHistorial.objects.filter(
            fecha_creacion__gte=fecha_limite
        ).order_by('-fecha_creacion')

def obtener_historial_ordenado_custom(dias=30, orden_descendente=True):
    """
    Nueva función que SIEMPRE usa Quick Sort personalizado
    
    Args:
        dias: Número de días hacia atrás
        orden_descendente: True para más reciente primero, False para más antiguo primero
    
    Returns:
        List de diccionarios ordenados con Quick Sort
    """
    from django.utils import timezone
    from datetime import timedelta
   
    fecha_limite = timezone.now() - timedelta(days=dias)
    
    # Obtener datos sin ordenar de la BD
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
            'fecha_creacion': actividad.fecha_creacion,
            'metadata': actividad.metadata,
            'objeto_id': actividad.objeto_id,
        })
    
    # ¡Usar nuestro Quick Sort!
    return quick_sort_historial(actividades_dict, orden_descendente)

def contar_actividades_hoy():
    """
    Cuenta las actividades para el día actual
    """
    from django.utils import timezone
   
    hoy = timezone.now().date()
    return ActividadHistorial.objects.filter(
        fecha_creacion__date=hoy
    ).count()

def obtener_estadisticas_globales(dias=7):
    """
    Obtiene estadísticas básicas globales
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count
   
    fecha_limite = timezone.now() - timedelta(days=dias)
   
    stats = ActividadHistorial.objects.filter(
        fecha_creacion__gte=fecha_limite
    ).values('app_origen').annotate(
        count=Count('id')
    ).order_by('-count')
   
    return {
        'total_actividades': sum(stat['count'] for stat in stats),
        'por_app': stats,
        'dias_analizados': dias
    }

def limpiar_historial_antiguo(dias=60):
    """
    Función opcional para limpiar actividades muy antiguas
    """
    from django.utils import timezone
    from datetime import timedelta
   
    fecha_limite = timezone.now() - timedelta(days=dias)
    eliminadas = ActividadHistorial.objects.filter(
        fecha_creacion__lt=fecha_limite
    ).count()
   
    ActividadHistorial.objects.filter(
        fecha_creacion__lt=fecha_limite
    ).delete()
   
    return eliminadas