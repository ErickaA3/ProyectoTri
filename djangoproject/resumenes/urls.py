# resumenes/urls.py
from django.urls import path
from . import views

app_name = 'resumenes'

urlpatterns = [
    path('', views.home, name='home'),  # ← Cambiado de resumenes_home a home
    path('process-file/', views.process_file, name='process_file'),
    path('process-text/', views.process_text, name='process_text'),
    path('summary/<int:document_id>/', views.view_summary, name='view_summary'),
]