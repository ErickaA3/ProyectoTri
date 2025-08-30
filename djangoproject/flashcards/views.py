from django.shortcuts import render

from django.shortcuts import render

def flashcards_home(request):
    context = {
        'titulo': 'Flashcards',
        'descripcion': 'Practica con tarjetas de memoria'
    }
    return render(request, 'flashcards/flashcards_home.html', context)
