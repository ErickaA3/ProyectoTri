# cuestionarios/urls.py
from django.urls import path
from . import views

app_name = 'cuestionarios'

urlpatterns = [
    path('', views.cuestionarios_home, name='home'),
    path('config/', views.config_cuestionario, name='config'),
    path('crear/', views.crear_cuestionario, name='create'),
    path('quiz/<int:quiz_id>/', views.mostrar_quiz, name='quiz'),
    path('responder/', views.responder_pregunta, name='answer'),
    path('resultados/<int:quiz_id>/', views.mostrar_resultados, name='results'),
    path('revisar/', views.revisar_respuestas, name='review'),
]