from django.urls import path, include
from . import views

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),
    path('obtener_historial/', views.obtener_historial, name='obtener_historial'),
    path('estadisticas_historial/', views.estadisticas_historial, name='estadisticas_historial'),
    # URLs de las apps existentes
    path('resumenes/', include('resumenes.urls')),
    path('esquemas/', include('esquemas.urls')),
    path('cuestionarios/', include('cuestionarios.urls')),
    path('flashcards/', include('flashcards.urls')),
]