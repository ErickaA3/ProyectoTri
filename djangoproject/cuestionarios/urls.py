from django.urls import path
from . import views

app_name = 'cuestionarios'

urlpatterns = [
    path('', views.cuestionarios_home, name='home'),
    path('config/', views.config_view, name='config'),  # Aquí defines la URL y el nombre 'config'
    # otras rutas...
]
