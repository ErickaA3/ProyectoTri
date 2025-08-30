from django.urls import path
from . import views

app_name = 'cuestionarios'

urlpatterns = [
    path('', views.cuestionarios_home, name='home'),
]