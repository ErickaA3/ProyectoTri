from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def resumenes_home(request):
    context = {
        'titulo': 'Resúmenes',
        'descripcion': 'Gestiona tus resúmenes de estudio'
    }
    return render(request, 'resumenes/resumenes_home.html', context)