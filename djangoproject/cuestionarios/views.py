from django.shortcuts import render

from django.shortcuts import render

def cuestionarios_home(request):
    context = {
        'titulo': 'Cuestionarios',
        'descripcion': 'Pon a prueba tus conocimientos'
    }
    return render(request, 'cuestionarios/cuestionarios_home.html', context)


from django.shortcuts import render

def config_view(request):
    context = {}  # Pasa los datos necesarios al contexto
    return render(request, 'cuestionarios/config.html', context)  # Renderiza la plantilla config.html
