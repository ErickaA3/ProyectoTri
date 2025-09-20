# urls.py - En tu proyecto principal
from django.urls import path, include
from . import views

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),
    
    # APIs del historial
    path('api/historial/', views.obtener_historial, name='obtener_historial'),
    path('api/estadisticas/', views.estadisticas_historial, name='estadisticas_historial'),
    
    # URLs de las apps existentes
    path('resumenes/', include('resumenes.urls')),
    path('esquemas/', include('esquemas.urls')),
    path('cuestionarios/', include('cuestionarios.urls')),
    path('flashcards/', include('flashcards.urls')),  # Si tienes esta app
]
