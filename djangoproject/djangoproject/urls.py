# En tu urls.py principal del proyecto (mi_proyecto/urls.py)

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

# Vista para la página de inicio (si no tienes una app principal)
def home(request):
    return render(request, 'home.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('resumenes/', include('resumenes.urls')),
    path('esquemas/', include('esquemas.urls')),
    path('flashcards/', include('flashcards.urls')),
    path('cuestionarios/', include('cuestionarios.urls')),
]