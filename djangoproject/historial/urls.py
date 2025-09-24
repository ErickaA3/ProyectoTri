# historial/urls.py
from django.urls import path
from . import views

app_name = 'historial'

urlpatterns = [
    # Vista principal del historial con ordenamiento
    path('', views.obtener_historial, name='obtener_historial'),
    
    # Estadísticas básicas
    path('estadisticas/', views.estadisticas_historial, name='estadisticas'),
]