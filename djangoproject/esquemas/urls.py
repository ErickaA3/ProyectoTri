# esquemas/urls.py
from django.urls import path
from . import views

app_name = 'esquemas'

urlpatterns = [
    # Vista principal
    path('', views.esquemas_home, name='home'),
    
    # Crear esquemas
    path('crear/texto/', views.crear_desde_texto, name='crear_desde_texto'),
    path('crear/archivo/', views.crear_desde_archivo, name='crear_desde_archivo'),
    
    # Ver y gestionar esquemas
    path('ver/<int:esquema_id>/', views.ver_esquema, name='ver_esquema'),
    path('mis-esquemas/', views.mis_esquemas, name='mis_esquemas'),
    path('eliminar/<int:esquema_id>/', views.eliminar_esquema, name='eliminar_esquema'),
    
    # Exportar esquemas
    path('exportar/<int:esquema_id>/pdf/', views.exportar_esquema_pdf, name='exportar_pdf'),
    path('exportar/<int:esquema_id>/txt/', views.exportar_esquema_txt, name='exportar_txt'),
    
    # API endpoints
    path('api/<int:esquema_id>/datos/', views.api_esquema_datos, name='api_esquema_datos'),
]