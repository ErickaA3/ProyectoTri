# cuestionarios/urls.py
from django.urls import path
from . import views

app_name = 'cuestionarios'

urlpatterns = [
    # URLs principales
    path('', views.cuestionarios_home, name='home'),
    path('config/', views.config_cuestionario, name='config'),
    path('crear/', views.crear_cuestionario, name='create'),
    path('quiz/<int:quiz_id>/', views.mostrar_quiz, name='quiz'),
    path('responder/<int:cuestionario_id>/', views.responder_pregunta, name='responder'),  
    path('resultados/<int:quiz_id>/', views.mostrar_resultados, name='results'),
    path('revisar/', views.revisar_respuestas, name='review'),
    
    # URLs para cuestionarios recientes
    path('mis-cuestionarios/', views.mis_cuestionarios, name='mis_cuestionarios'),
    path('ver/<int:cuestionario_id>/', views.ver_cuestionario, name='ver_cuestionario'),
    path('eliminar/<int:cuestionario_id>/', views.eliminar_cuestionario, name='eliminar_cuestionario'),
    path('exportar/pdf/<int:cuestionario_id>/', views.exportar_pdf_cuestionario, name='exportar_pdf'),
]