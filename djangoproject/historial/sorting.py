# historial/sorting.py
from datetime import datetime
from typing import List, Dict, Any

def quick_sort_historial(actividades: List[Dict], orden_descendente: bool = True):
    """
    Ordena actividades del historial usando Quick Sort por fecha_creacion
    """
    def _quicksort_fechas(lista, bajo, alto):
        if bajo < alto:
            pivot = dividir_por_fecha(lista, bajo, alto, orden_descendente)
            _quicksort_fechas(lista, bajo, pivot - 1)
            _quicksort_fechas(lista, pivot + 1, alto)
    
    if not actividades:
        return []
    
    # Crear copia para no modificar el original
    actividades_copia = actividades.copy()
    _quicksort_fechas(actividades_copia, 0, len(actividades_copia) - 1)
    return actividades_copia

def dividir_por_fecha(lista, bajo, alto, descendente):
    """Función auxiliar para particionar por fecha"""
    pivot_fecha = lista[alto]['fecha_creacion']
    i = bajo - 1
    
    for j in range(bajo, alto):
        actividad_fecha = lista[j]['fecha_creacion']
        
        # Comparación según el orden deseado
        if descendente:
            # Para orden descendente: fecha más reciente va primero
            condicion = actividad_fecha >= pivot_fecha
        else:
            # Para orden ascendente: fecha más antigua va primero
            condicion = actividad_fecha <= pivot_fecha
            
        if condicion:
            i += 1
            lista[i], lista[j] = lista[j], lista[i]
    
    lista[i + 1], lista[alto] = lista[alto], lista[i + 1]
    return i + 1