# historial/utils.py
from .models import ActividadHistorial

def registrar_actividad(tipo, titulo, descripcion="", app_origen="", objeto_id=None, metadata=None):
    """
    Función auxiliar para registrar una nueva actividad en el historial
    Sin sistema de usuarios - historial global
    
    Args:
        tipo: Tipo de actividad (debe estar en TIPOS_ACTIVIDAD del modelo)
        titulo: Título de la actividad
        descripcion: Descripción opcional
        app_origen: App donde se originó ('resumenes', 'esquemas', etc.)
        objeto_id: ID del objeto creado/modificado
        metadata: Diccionario con información adicional
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

def obtener_historial_reciente(dias=30):
    """
    Obtiene el historial de actividades recientes
    
    Args:
        dias: Número de días hacia atrás (default: 30)
    
    Returns:
        QuerySet de ActividadHistorial
    """
    from django.utils import timezone
    from datetime import timedelta
    
    fecha_limite = timezone.now() - timedelta(days=dias)
    return ActividadHistorial.objects.filter(
        fecha_creacion__gte=fecha_limite
    ).order_by('-fecha_creacion')

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