from django.urls import path
from . import views

app_name = 'flashcards'

urlpatterns = [
    # Cambiar esta línea
    path('', views.flashcards_home, name='flashcards_home'),
    
    # Por esta
    path('', views.flashcards_home, name='home'),
    
    # El resto permanece igual...
    path('process-file/', views.process_file, name='process_file'),
    path('process-text/', views.process_text, name='process_text'),
    path('collection/<uuid:collection_id>/', views.view_collection, name='view_collection'),
    path('my-flashcards/', views.my_flashcards, name='my_flashcards'),
    path('study/<uuid:collection_id>/', views.study_collection, name='study_collection'),
    path('session/<int:session_id>/complete/', views.complete_study_session, name='complete_study_session'),
    path('collection/<uuid:collection_id>/delete/', views.delete_collection, name='delete_collection'),
]