# historial/models.py - CORREGIDO
from django.db import models
from django.utils import timezone

class ActividadHistorial(models.Model):
    TIPOS_ACTIVIDAD = [
        ('resumen_creado', 'Resumen Creado'),
        ('esquema_generado', 'Esquema Generado'),  # ← CAMBIADO
        ('flashcards_creadas', 'Flashcards Creadas'),  # ← CAMBIADO
        ('flashcards_practicadas', 'Flashcards Practicadas'),  # ← CAMBIADO
        ('cuestionario_creado', 'Cuestionario Creado'),
        ('cuestionario_completado', 'Cuestionario Completado'),
    ]
    
    # Sin usuario - historial global
    tipo = models.CharField(max_length=30, choices=TIPOS_ACTIVIDAD)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    
    # Campos para almacenar IDs de los objetos relacionados
    objeto_id = models.CharField(max_length=50, null=True, blank=True)  # ID del resumen, esquema, etc.
    app_origen = models.CharField(max_length=20)  # 'resumenes', 'esquemas', etc.
    
    # Metadata adicional como JSON
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Actividad del Historial'
        verbose_name_plural = 'Actividades del Historial'
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"
