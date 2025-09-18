# esquemas/models.py
from django.db import models
from django.contrib.auth.models import User
import json

class Esquema(models.Model):
    TIPO_CHOICES = [
        ('jerarquico', 'Esquema Jerárquico'),
        ('conceptual', 'Mapa Conceptual'),
        ('cronologico', 'Línea de Tiempo'),
    ]
    
    FUENTE_CHOICES = [
        ('archivo', 'Archivo'),
        ('texto', 'Texto'),
    ]
    
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='jerarquico')
    fuente = models.CharField(max_length=20, choices=FUENTE_CHOICES)
    contenido_original = models.TextField()  # Texto original del usuario
    contenido_procesado = models.JSONField()  # Esquema generado por OpenAI
    archivo_original = models.FileField(upload_to='esquemas/archivos/', null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='esquemas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"
    
    def get_contenido_formateado(self):
        """Devuelve el contenido procesado de forma legible"""
        if isinstance(self.contenido_procesado, dict):
            return self.contenido_procesado
        return json.loads(self.contenido_procesado) if self.contenido_procesado else {}


class NodoEsquema(models.Model):
    """Modelo para representar nodos individuales en esquemas jerárquicos"""
    esquema = models.ForeignKey(Esquema, on_delete=models.CASCADE, related_name='nodos')
    texto = models.TextField()
    nivel = models.IntegerField(default=1)  # 1, 2, 3 para niveles de jerarquía
    orden = models.IntegerField(default=0)  # Orden dentro del nivel
    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='hijos')
    
    class Meta:
        ordering = ['nivel', 'orden']
        
    def __str__(self):
        return f"Nivel {self.nivel}: {self.texto[:50]}"


class EventoTimeline(models.Model):
    """Modelo para eventos en líneas de tiempo"""
    esquema = models.ForeignKey(Esquema, on_delete=models.CASCADE, related_name='eventos')
    fecha = models.CharField(max_length=50)  # Puede ser año, fecha completa, etc.
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    orden = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['orden']
        
    def __str__(self):
        return f"{self.fecha}: {self.titulo}"


class ConceptoMapa(models.Model):
    """Modelo para conceptos en mapas conceptuales"""
    esquema = models.ForeignKey(Esquema, on_delete=models.CASCADE, related_name='conceptos')
    texto = models.CharField(max_length=200)
    es_central = models.BooleanField(default=False)
    descripcion = models.TextField(blank=True)
    posicion_x = models.IntegerField(default=0)
    posicion_y = models.IntegerField(default=0)
    
    def __str__(self):
        return self.texto