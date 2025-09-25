from django.urls import path
from . import views

app_name = 'resumenes'

urlpatterns = [
    path('', views.home, name='home'),
    path('process-file/', views.process_file, name='process_file'),
    path('process-text/', views.process_text, name='process_text'),
    path('summary/<int:document_id>/', views.view_summary, name='view_summary'),
    path('mis-resumenes/', views.mis_resumenes, name='mis_resumenes'),
    path('ver/<int:id>/', views.ver_resumen, name='ver_resumen'),
    path('exportar-pdf/<int:id>/', views.exportar_pdf, name='exportar_pdf'),
    path('confirmar-eliminar/<int:id>/', views.confirmar_eliminar_resumen, name='confirmar_eliminar_resumen'),
    path('eliminar/<int:id>/', views.eliminar_resumen, name='eliminar_resumen'),
]