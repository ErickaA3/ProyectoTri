# cuestionarios/models.py
from django.db import models
from django.contrib.auth.models import User
import json

class Cuestionario(models.Model):
    DIFICULTAD_CHOICES = [
        ('facil', 'Fácil'),
        ('medio', 'Medio'),
        ('dificil', 'Difícil'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=200)
    contenido_original = models.TextField()  # El texto o contenido del archivo
    num_preguntas = models.IntegerField(default=10)
    dificultad = models.CharField(max_length=10, choices=DIFICULTAD_CHOICES, default='medio')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Cuestionario {self.id} - {self.usuario.username}"

class Pregunta(models.Model):
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE, related_name='preguntas')
    numero = models.IntegerField()  # Orden de la pregunta
    texto = models.TextField()
    opciones = models.JSONField()  # Lista de opciones de respuesta
    respuesta_correcta = models.IntegerField()  # Índice de la respuesta correcta
    
    class Meta:
        ordering = ['numero']
    
    def __str__(self):
        return f"Pregunta {self.numero} - {self.cuestionario.id}"

class RespuestaUsuario(models.Model):
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    respuesta_seleccionada = models.IntegerField(null=True, blank=True)  # Índice de la respuesta seleccionada
    es_correcta = models.BooleanField(default=False)
    fecha_respuesta = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cuestionario', 'pregunta']
    
    def __str__(self):
        return f"Respuesta {self.cuestionario.id} - Pregunta {self.pregunta.numero}"

class ResultadoCuestionario(models.Model):
    cuestionario = models.OneToOneField(Cuestionario, on_delete=models.CASCADE, related_name='resultado')
    puntuacion = models.FloatField()  # Porcentaje de aciertos
    respuestas_correctas = models.IntegerField()
    respuestas_incorrectas = models.IntegerField()
    total_preguntas = models.IntegerField()
    tiempo_completado = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Resultado {self.cuestionario.id} - {self.puntuacion}%"