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
        verbose_name = 'Esquema'
        verbose_name_plural = 'Esquemas'
        
    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"
    
    def get_contenido_formateado(self):
        """Devuelve el contenido procesado de forma legible"""
        if isinstance(self.contenido_procesado, dict):
            return self.contenido_procesado
        return json.loads(self.contenido_procesado) if self.contenido_procesado else {}
    
    def tiene_nodos(self):
        """Verifica si el esquema jerárquico tiene nodos en la BD"""
        if self.tipo == 'jerarquico':
            return self.nodos.exists()
        return False
    
    def tiene_eventos(self):
        """Verifica si el esquema cronológico tiene eventos en la BD"""
        if self.tipo == 'cronologico':
            return self.eventos.exists()
        return False
    
    def tiene_conceptos(self):
        """Verifica si el esquema conceptual tiene conceptos en la BD"""
        if self.tipo == 'conceptual':
            return self.conceptos.exists()
        return False


class NodoEsquema(models.Model):
    """Modelo mejorado para nodos jerárquicos con información expandible"""
    esquema = models.ForeignKey(Esquema, on_delete=models.CASCADE, related_name='nodos')
    texto = models.TextField()
    nivel = models.IntegerField(default=1)  # 1, 2, 3 para niveles de jerarquía
    orden = models.IntegerField(default=0)  # Orden dentro del nivel
    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='hijos')
    
    # Campos nuevos para información expandible
    detalles = models.TextField(blank=True, help_text="Información adicional expandible")
    palabras_clave = models.JSONField(default=list, blank=True, help_text="Lista de palabras clave")
    importancia = models.CharField(
        max_length=10, 
        choices=[('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')],
        default='media'
    )
    
    class Meta:
        ordering = ['nivel', 'orden']
        verbose_name = 'Nodo de Esquema'
        verbose_name_plural = 'Nodos de Esquema'
        
    def __str__(self):
        return f"Nivel {self.nivel}: {self.texto[:50]}"
    
    def es_raiz(self):
        """Verifica si es un nodo raíz (sin padre)"""
        return self.padre is None
    
    def tiene_hijos(self):
        """Verifica si el nodo tiene hijos"""
        return self.hijos.exists()
    
    def count_hijos(self):
        """Cuenta el número de hijos directos"""
        return self.hijos.count()
    
    def get_ruta_completa(self):
        """Obtiene la ruta completa desde la raíz hasta este nodo"""
        ruta = []
        nodo_actual = self
        while nodo_actual:
            ruta.insert(0, nodo_actual.texto[:30])
            nodo_actual = nodo_actual.padre
        return ' > '.join(ruta)
    
    def get_palabras_clave_str(self):
        """Devuelve las palabras clave como string separado por comas"""
        if isinstance(self.palabras_clave, list):
            return ', '.join(self.palabras_clave)
        return ''
    
    def tiene_detalles(self):
        """Verifica si el nodo tiene información adicional"""
        return bool(self.detalles.strip())


class EventoTimeline(models.Model):
    """Modelo mejorado para eventos en líneas de tiempo"""
    esquema = models.ForeignKey(Esquema, on_delete=models.CASCADE, related_name='eventos')
    fecha = models.CharField(max_length=50)  # Puede ser año, fecha completa, etc.
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    orden = models.IntegerField(default=0)
    
    # Campos nuevos para información expandible
    importancia = models.CharField(
        max_length=10, 
        choices=[('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')],
        default='media'
    )
    contexto = models.TextField(blank=True, help_text="Contexto histórico o situacional")
    consecuencias = models.JSONField(default=list, blank=True, help_text="Lista de consecuencias")
    
    class Meta:
        ordering = ['orden']
        verbose_name = 'Evento de Timeline'
        verbose_name_plural = 'Eventos de Timeline'
        
    def __str__(self):
        return f"{self.fecha}: {self.titulo}"
    
    def get_consecuencias_str(self):
        """Devuelve las consecuencias como string"""
        if isinstance(self.consecuencias, list):
            return ', '.join(self.consecuencias)
        return ''


class ConceptoMapa(models.Model):
    """Modelo mejorado para conceptos en mapas conceptuales"""
    esquema = models.ForeignKey(Esquema, on_delete=models.CASCADE, related_name='conceptos')
    texto = models.CharField(max_length=200)
    es_central = models.BooleanField(default=False)
    descripcion = models.TextField(blank=True)
    posicion_x = models.IntegerField(default=0)
    posicion_y = models.IntegerField(default=0)
    
    # Campos nuevos para información expandible
    importancia = models.CharField(
        max_length=10, 
        choices=[('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')],
        default='media'
    )
    conexiones = models.JSONField(default=list, blank=True, help_text="Lista de conceptos relacionados")
    ejemplos = models.JSONField(default=list, blank=True, help_text="Ejemplos del concepto")
    
    class Meta:
        verbose_name = 'Concepto de Mapa'
        verbose_name_plural = 'Conceptos de Mapa'
    
    def __str__(self):
        tipo = "Central" if self.es_central else "Relacionado"
        return f"{self.texto} ({tipo})"
    
    def get_conexiones_str(self):
        """Devuelve las conexiones como string"""
        if isinstance(self.conexiones, list):
            return ', '.join(self.conexiones)
        return ''
    
    def get_ejemplos_str(self):
        """Devuelve los ejemplos como string"""
        if isinstance(self.ejemplos, list):
            return ', '.join(self.ejemplos)
        return ''