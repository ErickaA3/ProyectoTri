from django.urls import path
from . import views

app_name = 'flashcards'

urlpatterns = [
    # Vista principal
    path('', views.flashcards_home, name='home'),
    path('', views.flashcards_home, name='flashcards_home'),
    
    # Procesamiento
    path('process-file/', views.process_file, name='process_file'),
    path('process-text/', views.process_text, name='process_text'),
    
    # Visualización
    path('collection/<uuid:collection_id>/', views.view_collection, name='view_collection'),
    path('my-flashcards/', views.my_flashcards, name='my_flashcards'),
    
    # Estudio
    path('study/<uuid:collection_id>/', views.study_collection, name='study_collection'),
    path('session/<int:session_id>/complete/', views.complete_study_session, name='complete_study_session'),
    
    # Eliminación con confirmación
    path('collection/<uuid:collection_id>/eliminar/', views.confirmar_eliminar_collection, name='confirmar_eliminar_collection'),
    
    # Eliminación AJAX (mantener para compatibilidad)
    path('collection/<uuid:collection_id>/delete/', views.delete_collection, name='delete_collection'),
]