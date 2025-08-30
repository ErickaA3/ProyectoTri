from django.shortcuts import render

from django.shortcuts import render

def cuestionarios_home(request):
    context = {
        'titulo': 'Cuestionarios',
        'descripcion': 'Pon a prueba tus conocimientos'
    }
    return render(request, 'cuestionarios/cuestionarios_home.html', context)
