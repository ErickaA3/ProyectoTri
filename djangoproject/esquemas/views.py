from django.shortcuts import render

from django.shortcuts import render

def esquemas_home(request):
    context = {
        'titulo': 'Esquemas',
        'descripcion': 'Crea y organiza tus esquemas de estudio'
    }
    return render(request, 'esquemas/esquemas_home.html', context)
